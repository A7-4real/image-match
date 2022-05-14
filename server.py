from elasticsearch import Elasticsearch
from flask import Flask, request
from flask_cors import CORS
# from flask import Blueprint

from image_match.elasticsearch_driver import SignatureES
from image_match.goldberg import ImageSignature
import json
import os


# Globals values


# es_url = os.environ['http://127.0.0.1:9200/']        # localhost (by default)
es_url = 'http://127.0.0.1:9200/'
# es_index = os.environ['images']                      # index name
es_index = 'images'
# es_doc_type = os.environ['image']                    # doc_type
es_doc_type = 'image'
# all_orientations = os.environ['ALL_ORIENTATIONS']
all_orientations = 'ALL_ORIENTATIONS'

# blueprint = Blueprint('blueprint', __name__)

app = Flask(__name__)
cors = CORS(app, resources={r"/imagesearch/*": {"origins": "*"}})
es = Elasticsearch([es_url], verify_certs=True, timeout=60,
                   max_retries=10, retry_on_timeout=True)
ses = SignatureES(es, index=es_index, doc_type=es_doc_type)
gis = ImageSignature()

# Try to create the index and ignore IndexAlreadyExistsException
# if the index already exists
es.indices.create(index=es_index, ignore=400)

# Helper functions


def get_image(url_field, file_field):
    if url_field in request.form:
        return request.form[url_field], False
    else:
        return request.files[file_field].read(), True


def count_images():
    return es.count(index=es_index)['count']


def delete_ids(ids):
    for i in ids:
        es.delete(index=es_index, doc_type=es_doc_type, id=i, ignore=404)


def dist_to_percent(dist):
    return (1 - dist) * 100


def ids_with_path(path):
    matches = es.search(index=es_index,
                        _source='_id',
                        q='path:' + json.dumps(path))
    return [m['_id'] for m in matches['hits']['hits']]


# # Blueprint

# @blueprint.after_request
# def after_request(response):
#     header = response.headers
#     header['Access-Control-Allow-Origin'] = '*'
#     # Other headers can be added here if needed
#     return response

# Routes


@app.route('/', methods=['GET', 'POST'])
def welcome():
    return "hello World!"


@app.route('/imagesearch/<string:url>', methods=['GET', 'POST'])
def searhImage(url):
    modified_url = url.replace("7slash7", "/")
    matches = ses.search_image(modified_url)
    return json.dumps(matches)


@app.route('/search', methods=['GET', 'POST'])
def search_handler():
    img, bs = get_image('url', 'image')
    ao = request.form.get('all_orientations', all_orientations) == 'true'

    matches = ses.search_image(
        path=img,
        all_orientations=ao,
        bytestream=bs)

    return json.dumps({
        'status': 'ok',
        'error': [],
        'method': 'search',
        'result': [{
            'score': dist_to_percent(m['dist']),
            'filepath': m['path'],
            'metadata': m['metadata']
        } for m in matches]
    })


@app.route('/delete', methods=['DELETE'])
def delete_handler():
    path = request.form['filepath']
    ids = ids_with_path(path)
    delete_ids(ids)
    return json.dumps({
        'status': 'ok',
        'error': [],
        'method': 'delete',
        'result': []
    })


@app.route('/count', methods=['GET', 'POST'])
def count_handler():
    count = count_images()
    return json.dumps({
        'status': 'ok',
        'error': [],
        'method': 'count',
        'result': [count]
    })


if __name__ == '__main__':
    app.run(debug=True)

# =============================================================================
# Error Handlers


@app.errorhandler(400)
def bad_request(e):
    return json.dumps({
        'status': 'fail',
        'error': ['bad request'],
        'method': '',
        'result': []
    }), 400


@app.errorhandler(404)
def page_not_found(e):
    return json.dumps({
        'status': 'fail',
        'error': ['not found'],
        'method': '',
        'result': []
    }), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return json.dumps({
        'status': 'fail',
        'error': ['method not allowed'],
        'method': '',
        'result': []
    }), 405


@app.errorhandler(500)
def server_error(e):
    return json.dumps({
        'status': 'fail',
        'error': [str(e)],
        'method': '',
        'result': []
    }), 500
