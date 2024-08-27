#!/usr/bin/env python

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    g,
    flash,
    make_response,
    send_from_directory,
    Response,
    send_file,
)
from werkzeug.utils import secure_filename
import jinja2

import pprint

import subprocess
import pathlib
import os
import sys
import shutil
import datetime
import time
import json
import csv
import tempfile
import re

import record as cdb
## from pymongo import MongoClient
## mongo_client = MongoClient('localhost', 27017)
## db = mongo_client['colabfit']
## coll_configuration_sets = db['configuration_sets']
##
## # db.list_collection_names()
##
## pprint.pprint(coll_configuration_sets.find_one())
##
## # coll_configuration_sets.find_one()['relationships']['datasets']
##
## pprint.pprint(coll_configuration_sets.find_one({"colabfitid": "CS_106781881599_000"}))
##
## for item in coll_configuration_sets.find():
##     pprint.pprint( item['colabfitid'] )
##
## for item in coll_configuration_sets.find( {"colabfitid": {"$in": ["CS_106781881599_000"] } } ):
##     pprint.pprint( item['colabfitid'] )
##
## for dataset in cdb.dataset_all():
##     pprint.pprint( dataset )


#a = cdb.abc()
#pprint.pprint(a)


# use admin
# db.createUser({
#   user: "materials_reader",
#   pwd: "materials_reader",
#   roles: [{role: "read", db: "colabfit"}]
# })
#
# % mongo -u materials_reader --authenticationDatabase admin


COLABFITSPEC_DOMAIN = 'materials.colabfit.org'
URL_START = f"https://{COLABFITSPEC_DOMAIN}"
TEMPLATE__SITE__PATH_STATIC_SITE = "https://colabfit.org"
TEMPLATE__SITE__PATH_DYNAMIC_SITE = "https://materials.colabfit.org"

app = Flask(__name__, static_folder='static', static_url_path='')

# Reduce browser 304 requests
# https://flask.palletsprojects.com/en/2.2.x/config/#SEND_FILE_MAX_AGE_DEFAULT
app.config['SEND_FILE_MAX_AGE_DEFAULT']=300


class dotdict(dict):
    __getattr__ = dict.get

# https://flask.palletsprojects.com/en/3.0.x/templating/#context-processors
@app.context_processor
def inject_global_template_shared_site_definitions():
    site = dotdict({})
    site['path_static_site'] = TEMPLATE__SITE__PATH_STATIC_SITE
    site['path_dynamic_site'] = TEMPLATE__SITE__PATH_DYNAMIC_SITE
    return dict(site=site)


@app.template_filter()
def j2_filter_subscript_numbers(input):
    return re.sub(r'(\d+)', r'<sub>\1</sub>', input)

@app.template_filter()
def j2_filter_property_id_to_urlpath(input):
    return property_id_to_urlpath( input )


def property_id_to_urlpath( property_id ):
    #property_id = "tag:staff@noreply.colabfit.org,2022-05-30:property/free-energy"
    match = re.search(r'tag:(?P<email>.*),(?P<date>\d\d\d\d-\d\d-\d\d):property/(?P<property_id_simple>.*)$', property_id)
    str = '/'.join([ match.group('date'), match.group('email'), match.group('property_id_simple')])
    return str


def property_id_components_to_full_property_id( date, email, property_id_simple ):
    str = f"tag:{email},{date}:property/{property_id_simple}"
    return str


def two_letter_code_to_name_with_underscores( two_letter_code ):
    two_letter_code = two_letter_code.lower()
    ret = None
    match two_letter_code:
        case 'cs':
            ret = 'configuration_set'
        case 'co':
            ret = 'configuration'
        case 'do':
            ret = 'data_object'
        case 'ds':
            ret = 'dataset'
        case 'pi':
            ret = 'property_instance'
        case 'md':
            ret = 'metadata'
        case _:
            raise Exception("Unknown two letter code")
    return ret


def colabfitid_to_two_letter_code( colabfitid ):
    return colabfitid[0:2]

def colabfitid_to_name_with_underscores( colabfitid ):
    return( two_letter_code_to_name_with_underscores(
                colabfitid_to_two_letter_code( colabfitid ) ) )


# https://stackoverflow.com/a/66127889
def delete_none_values_from_dict(_dict):
    """Delete None values recursively from all of the dictionaries, tuples, lists, sets"""
    if isinstance(_dict, dict):
        for key, value in list(_dict.items()):
            if isinstance(value, (list, dict, tuple, set)):
                _dict[key] = delete_none_values_from_dict(value)
            elif value is None or key is None:
                del _dict[key]

    elif isinstance(_dict, (list, set, tuple)):
        _dict = type(_dict)(delete_none_values_from_dict(item) for item in _dict if item is not None)

    return _dict


def build_initial_colabfitspec( m ):
    m.pop('_id', None)
    m.pop('last_modified', None)
    m.update({'domain': COLABFITSPEC_DOMAIN})
    m = delete_none_values_from_dict(m)
    return m

#j = cdb.bson.json_util.dumps(item)

# @app.route('/', methods=['GET'])
# def index():
#     #configuration_set_count = 1
#     #configuration_count = 1
#     #dataset_count = 1
#     #property_instance_count = 1
#     #property_definition_count = 1
#     #metadata_count = 1
#
#     configuration_set_count = cdb.configuration_set_count()
#     #configuration_count = cdb.configuration_count()
#     #data_object_count = cdb.data_object_count()
#     dataset_count = cdb.dataset_count()
#     #property_instance_count = cdb.property_instance_count()
#     property_definition_count = cdb.property_definition_count()
#     #metadata_count = cdb.metadata_count()
#
#     #print( cdb.property_instance_count() )
#     #print( cdb.configuration_count() )
#
#     return render_template('index.html',    configuration_set_count=configuration_set_count,
#                                             #configuration_count=configuration_count,
#                                             #data_object_count=data_object_count,
#                                             dataset_count=dataset_count,
#                                             #property_instance_count=property_instance_count,
#                                             property_definition_count=property_definition_count,
#                                             #metadata_count=metadata_count
#                                             )



@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    lines_begin = [ '<?xml version="1.0" encoding="UTF-8"?>',
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines_additional = [
        f"<url><loc>{URL_START}</loc></url>",
     ]
    lines_end = ['</urlset>']

    items1 = list( map( lambda x: x['colabfit-id'], cdb.dataset_all_nolimit_sortonname() ))
    items2 = list( map( lambda x: x['colabfit-id'], cdb.configuration_set_all_nolimit_sortonname() ))
    lines  = list( map( lambda x: f"<url><loc>{URL_START}/id/{x}</loc></url>", items1 + items2 ))
    xml = "\n".join(lines_begin + lines_additional + lines + lines_end)
    response = Response(
        response=xml,
        status=200,
        mimetype='application/xml'
    )
    return response


@app.route('/', methods=['GET'])
def index():
    periodic_table_data_json = open('periodic-table-data.json').read()
    request_values_preserve_multiple = request.values.to_dict(flat=False)
    search_parameters_supplied = False
    search_performed_but_no_results = False

    results = []
    number_of_results = 0
    param_args = {}
    param_args['name']                          = request.values.get('search-name')
    param_args['authors']                       = request.values.get('search-authors')
    param_args['description']                   = request.values.get('search-description')
    param_args['doi']                           = request.values.get('search-doi')
    param_args['elements']                      = request_values_preserve_multiple.get('search-elements[]',[])
    param_args['min_co']                        = request.values.get('search-number-of-configurations-min')
    param_args['max_co']                        = request.values.get('search-number-of-configurations-max')
    param_args['min_elements']                  = request.values.get('search-number-of-elements-min')
    param_args['max_elements']                  = request.values.get('search-number-of-elements-max')
    param_args['min_atoms']                     = request.values.get('search-number-of-atoms-min')
    param_args['max_atoms']                     = request.values.get('search-number-of-atoms-max')
    param_args['property_types']                = request_values_preserve_multiple.get('search-property-types[]',[])
    param_args['elements_match_only_selected']  = request.values.get('search-elements-match-only-selected')
    param_args['given_sort_by']                 = request.values.get('search-sort-by')
    param_args['given_sort_direction']          = request.values.get('search-sort-direction')


    results = []
    if( len(request.values) > 0 ):
        results = cdb.demoquerydatasets( **param_args )
        search_parameters_supplied = True
    else:
        results = cdb.demoquerydatasets()

    results = list(results)
    number_of_results = len(results)
    if number_of_results == 0:
        search_performed_but_no_results = True



    all_elements = ["Mg", "Yb", "He", "Ra", "Ta", "At", "Ca", "Nd", "Ru", "Be", "Ag", "Bh", "Fr", "O", "Tl", "Rn", "Ds", "F", "Mc", "Zr", "Ar", "Y", "I", "Si", "K", "Sm", "Ce", "Md", "Rb", "Pr", "Sc", "Mn", "Zn", "Sn", "B", "Co", "Eu", "Bk", "Nb", "Rg", "As", "Cr", "Tm", "Rh", "C", "Cn", "Pd", "Am", "Bi", "Pm", "Kr", "P", "Re", "Pa", "Ge", "Nh", "Cd", "Sg", "Db", "Ho", "Ts", "W", "Og", "Na", "Lv", "La", "Cf", "Er", "Th", "Au", "Ni", "Lr", "Hf", "H", "U", "Ba", "Mt", "Gd", "Ti", "Sb", "Fe", "Es", "Hs", "Ir", "Li", "Tc", "Ga", "Cu", "Te", "No", "Mo", "Br", "Os", "Ne", "Cl", "Pt", "Cm", "Xe", "Np", "Al", "Ac", "Tb", "Fl", "Rf", "Po", "In", "Pb", "V", "Fm", "Sr", "Dy", "Lu", "Pu", "Cs", "N", "Se", "Hg", "S"]
    existing_elements = cdb.coll_dataset.distinct("aggregated_info.elements")
    unavailable_elements = set(all_elements) - set(existing_elements)

    existing_property_types = cdb.coll_dataset.distinct("aggregated_info.property_types")

    configuration_set_count = cdb.configuration_set_count()
    dataset_count = cdb.dataset_count()
    property_definition_count = cdb.property_definition_count()

    return render_template('index.html',    results=results,
                                            search_performed_but_no_results=search_performed_but_no_results,
                                            search_parameters_supplied=search_parameters_supplied,
                                            number_of_results=number_of_results,
                                            param_args=param_args,
                                            existing_elements=existing_elements,
                                            unavailable_elements=unavailable_elements,
                                            existing_property_types=existing_property_types,
                                            periodic_table_data_json=periodic_table_data_json,
                                            configuration_set_count=configuration_set_count,
                                            dataset_count=dataset_count,
                                            property_definition_count=property_definition_count,
                                            )


#########
# Browse
##########

@app.route('/browse', methods=['GET'])
def browse_index():
    return render_template('browse/index.html')

@app.route('/browse/configuration-sets', methods=['GET'])
def browse_configuration_sets():
    #items = cdb.configuration_set_all()
    items = []
    return render_template('browse/configuration-sets.html', items=items, c="normal")

@app.route('/browse/configuration-sets-<string:s>', methods=['GET'])
def browse_configuration_sets_oc20(s):
    h = {   'oc20is2re': 'OC20 IS2RE',
            'oc20md': 'OC20 MD',
            'oc20rattled': 'OC20 Rattled',
            'oc20s3ef': 'OC20 S2EF' }
    if s not in h.keys():
        not_found_response("")

    items = []
    return render_template('browse/configuration-sets.html', items=items, c=h[s].replace(' ','_'), n=f"{h[s]} ")

@app.route('/browse/configurations', methods=['GET'])
def browse_configurations():
    items = cdb.configuration_all()
    return render_template('browse/configurations.html', items=items)

@app.route('/browse/data-objects', methods=['GET'])
def browse_data_objects():
    items = cdb.data_object_all()
    return render_template('browse/data-objects.html', items=items)

@app.route('/browse/datasets', methods=['GET'])
def browse_datasets():
    #items = cdb.dataset_all()
    items = []
    return render_template('browse/datasets.html', items=items, c="normal")

@app.route('/browse/datasets-<string:s>', methods=['GET'])
def browse_datasets_oc20(s):
    h = {   'oc20is2re': 'OC20 IS2RE',
            'oc20md': 'OC20 MD',
            'oc20rattled': 'OC20 Rattled',
            'oc20s3ef': 'OC20 S2EF' }
    if s not in h.keys():
        not_found_response("")

    #items = cdb.dataset_all()
    items = []
    return render_template('browse/datasets.html', items=items, c=h[s].replace(' ','_'), n=f"{h[s]} ")

@app.route('/browse/property-instances', methods=['GET'])
def browse_property_instances():
    items = cdb.property_instance_all()
    return render_template('browse/property-instances.html', items=items)



@app.route('/browse/property-definitions', methods=['GET'])
def browse_property_definitions():
    items = cdb.property_definition_all()
    #j_str = cdb.bson.json_util.dumps(items) )
    #for item in items:
    ##print( list(items) )
    #    j_str = json.dumps(item, indent = 4)
    #    print( j_str )

    return render_template('browse/property-definitions.html', items=items)


def not_found_response(s="ColabFit ID "):
    response = make_response(f"{s}Not Found", 404)
    response.mimetype = "text/plain"
    return response


def render_configuration_set(colabfitid):
    item                    = cdb.configuration_set_one(colabfitid)
    if not item: return not_found_response()
    dataset_ids             = cdb.configuration_set_relationship_dataset_all_ids( colabfitid )
    configuration_ids       = cdb.configuration_set_relationship_configuration_all_ids( colabfitid )
    return render_template(f"items/configuration_set.html",
                            item=item,
                            dataset_ids=dataset_ids,
                            configuration_ids=configuration_ids)

def render_configuration(colabfitid):
    item                    = cdb.configuration_one(colabfitid)
    if not item: return not_found_response()
    data_object_ids         = cdb.configuration_relationship_data_object_all_ids( colabfitid )
    configuration_set_ids   = cdb.configuration_relationship_configuration_set_all_ids( colabfitid )
    return render_template(f"items/configuration.html",
                            item=item,
                            data_object_ids=data_object_ids,
                            configuration_set_ids=configuration_set_ids)

def render_data_object(colabfitid):
    item                    = cdb.data_object_one(colabfitid)
    if not item: return not_found_response()
    configuration_id        = cdb.data_object_relationship_configuration_id( colabfitid )
    property_instance_ids   = cdb.data_object_relationship_property_instance_all_ids( colabfitid )
    dataset_ids             = cdb.data_object_relationship_dataset_all_ids( colabfitid )
    metadata_ids             = cdb.data_object_relationship_metadata_all_ids( colabfitid )
    return render_template(f"items/data-object.html",
                            item=item,
                            configuration_id=configuration_id,
                            property_instance_ids=property_instance_ids,
                            dataset_ids=dataset_ids,
                            metadata_ids=metadata_ids)


def generate_dataset_schema_org(item):
    colabfitid = item["colabfit-id"]

    # could also do request.path
    this_url = f"{URL_START}/id/{colabfitid}"
    name_converted = item["name"].replace('_', ' ')

    # Create a JSON object conforming to schema.org
    # See https://schema.org/Dataset
    # Note the ColabFit item name "Dataset" and the schema name "Dataset" are a coincidence
    #
    # Validate with https://validator.schema.org/
    #
    sod = {
        "@context": "https://schema.org",
        "@id": this_url,
        "@type": "Dataset",
        "url": this_url,
        "name": name_converted,
        "alternateName": item["extended-id"],
        #"url": [{"@type": "URL", "url": x} for x in item.get("links", [])],
        "publisher": {
            "@type": "Organization",
            "name": "ColabFit",
            "url": "https://colabfit.org",
            "logo": "https://colabfit.org/images/colabfit-logo-600.png",
        },
    }
    sod_keywords = [
        item["colabfit-id"],
        item["extended-id"],
        item["name"],
        name_converted,
    ]
    sod[ "keywords" ] = sod_keywords

    sod_archived_at = [f"{URL_START}/dataset-xyz/{ item['extended-id'] }.xyz.xz",
                        f"{URL_START}/files/{ item['colabfit-id'] }/colabfitspec.json"]
    sod_archived_at += item.get("links", [])
    sod[ "archivedAt" ] = sod_archived_at

    if item.get("authors"):
        sod["creator"] = [{"@type": "Person", "name": x} for x in item["authors"]]
    if item.get("description"):
        sod["description"] = item["description"]
    if item.get("license"):
        if item["license"] == "CC0":
            sod["license"] = "https://creativecommons.org/publicdomain/zero/1.0/"
        else:
            sod["license"] = item["license"]

    return json.dumps(sod, indent=2)


def generate_dataset_citation_string(item):
    joined_names_string = None
    joined_names = []

    for author in item['authors']:
        name_parts_orig = author.split(' ')
        name_parts_new = []
        family_name = name_parts_orig.pop()
        for name_part in name_parts_orig:
            # skip name parts that start as lower case
            if name_part[0].islower():
                continue
            s = name_part[0] + "."
            name_parts_new.append(s)

        formatted_name = family_name + ", " + " ".join(name_parts_new)
        joined_names.append( formatted_name )

    if( len(joined_names) > 1 ):
        joined_names[-1] = "and " + joined_names[-1]

    joined_names_string = ", ".join(joined_names)
    item_name_converted = item["name"].replace('_', ' ')
    citation_string = f"{joined_names_string} \"{item_name_converted}.\" ColabFit, {item['publication-year']}. https://doi.org/{item['doi']}."
    return citation_string


def render_dataset(colabfitid):
    item = cdb.dataset_one(colabfitid)
    if not item: return not_found_response()

    schema_org_data = generate_dataset_schema_org(item)
    citation_string = generate_dataset_citation_string(item)

    configuration_set_ids       = cdb.dataset_relationship_configuration_set_all_ids( colabfitid )
    configuration_set_objects   = cdb.dataset_relationship_configuration_set_all_objects( colabfitid )
    data_object_limit = 10_000
    data_object_ids             = cdb.dataset_relationship_data_object_all_ids_with_find_limit( colabfitid, data_object_limit )
    #data_objects_count          = cdb.dataset_relationship_data_object_count( colabfitid )
    data_objects_count          = item["aggregated_info"]["ndata_object"]
    return render_template(f"items/dataset.html",
                            item=item,
                            schema_org_data=schema_org_data,
                            citation_string=citation_string,
                            configuration_set_ids=configuration_set_ids,
                            configuration_set_objects=configuration_set_objects,
                            data_object_limit=data_object_limit,
                            data_object_ids=data_object_ids,
                            data_objects_count=data_objects_count,)

def render_property_instance(colabfitid):
    item                    = cdb.property_instance_one(colabfitid)
    if not item: return not_found_response()
    data_object_ids         = cdb.property_instance_relationship_data_object_all_ids( colabfitid )
    return render_template(f"items/property-instance.html",
                            item=item,
                            data_object_ids=data_object_ids)

def render_metadata(colabfitid):
    item                    = cdb.metadata_one(colabfitid)
    if not item: return not_found_response()
    data_object_ids   = cdb.metadata_relationship_data_object_all_ids( colabfitid )

    return render_template(f"items/metadata.html",
                            item=item,
                            data_object_ids=data_object_ids)



from werkzeug.routing import BaseConverter

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

@app.route('/id/<regex("[0-9]+"):numid>')
def baditem( numid ):
    return redirect(url_for('index'))


@app.route('/properties/raw/<property_id_simple1>/<p_date_and_email>/<property_id_simple2>.edn', methods=['GET'])
def show_property_definition_raw( p_date_and_email, property_id_simple1, property_id_simple2 ):
    if( property_id_simple1 != property_id_simple2 ):
        return redirect(url_for('index'))

    try:
        match = re.search(r'^(?P<p_date>\d\d\d\d-\d\d-\d\d)-(?P<p_email>.*)$', p_date_and_email)
        p_date = match.group('p_date')
        p_email = match.group('p_email')
    except:
        return redirect(url_for('index'))

    property_id = property_id_components_to_full_property_id( p_date, p_email, property_id_simple1 )
    item = cdb.property_definition_one( property_id )
    j_str = json.dumps( item['definition'], indent = 4)
    return j_str, 200, {"Content-Type": "application/json; charset=utf-8"}


@app.route('/properties/show/<p_date>/<p_email>/<property_id_simple>', methods=['GET'])
def show_property( p_date, p_email, property_id_simple ):
    property_id = property_id_components_to_full_property_id( p_date, p_email, property_id_simple )
    item = cdb.property_definition_one( property_id )
    property_urlpath = f"/properties/show/{property_id_to_urlpath( property_id )}"
    property_rawpath = f"/properties/raw/{ property_id_simple }/{ p_date }-{ p_email }/{ property_id_simple }.edn"
    return render_template(f"items/property-definition.html",   item=item,
                                                                property_id_date=p_date,
                                                                property_id=property_id,
                                                                property_urlpath=property_urlpath,
                                                                property_rawpath=property_rawpath,
                                                                property_id_simple=property_id_simple)


@app.route('/id/<colabfitid>', methods=['GET'])
def item( colabfitid ):
    # TODO: check if valid ID format
    name_with_underscores = colabfitid_to_name_with_underscores( colabfitid )
    function_to_call_str = f"render_{name_with_underscores}"
    result = globals()[function_to_call_str]( colabfitid )
    return( result )


@app.route('/files/<colabfitid>/colabfitspec.json', methods=['GET'])
def file_colabfitspec( colabfitid ):
    name_with_underscores = colabfitid_to_name_with_underscores( colabfitid )
    # call function with name "{name_with_underscores}_one" in cdb module
    item = getattr(cdb, f"{name_with_underscores}_one")( colabfitid )
    colabfitspec = build_initial_colabfitspec( item )
    j_str = json.dumps(item, indent = 4)
    return j_str, 200, {"Content-Type": "application/json; charset=utf-8"}


@app.route('/dbstats.json', methods=['GET'])
def dbstats_json():
    dbstats_dict = {
        'configuration_set_count':      "{:,}".format( cdb.configuration_set_count() ),
        'configuration_count':          "{:,}".format( cdb.configuration_count() ),
        'dataset_count':                "{:,}".format( cdb.dataset_count() ),
        'property_instance_count':      "{:,}".format( cdb.property_instance_count() ),
    #    'property_definition_count':    "{:,}".format( cdb.property_definition_count() ),
    #    'metadata_count':               "{:,}".format( cdb.metadata_count() ),
        'dataset_last_modified':        cdb.dataset_last_modified(),
    }
    # could also use flask.jsonify here
    j_str = json.dumps(dbstats_dict)
    response = Response(
        response=j_str,
        status=200,
        mimetype='application/json'
    )
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


######################################
######################################
##
## END ROUTES
##
######################################
######################################


def write_file_global_cache_data(data, filename):
    print(f"Writing static/js/{filename}")
    with open(f"static/js/{filename}", "w") as outfile:
        outfile.write( 'const global_cache_data = ' )
        # reduce white space, default separators are (', ', ': ')
        outfile.write( json.dumps(data, separators=(',', ':')) )
        outfile.write( ";\n" )


def write_file_javascript_cache_data_for_datasets():
    items = cdb.dataset_all_nolimit_sortonname()
    a_OC20_IS2RE = []
    a_OC20_MD = []
    a_OC20_Rattled = []
    a_OC20_S2EF = []
    a_without_o = []
    for item in items:
        thing_to_append = [item['colabfit-id'], {'n': item['name'], 'd': item['description']}]
        if item['name'].startswith('OC20_IS2RE'):
            a_OC20_IS2RE.append( thing_to_append )

        elif item['name'].startswith('OC20_MD'):
            a_OC20_MD.append( thing_to_append )

        elif item['name'].startswith('OC20_Rattled'):
            a_OC20_Rattled.append( thing_to_append )

        elif item['name'].startswith('OC20_S2EF'):
            a_OC20_S2EF.append( thing_to_append )

        else:
            a_without_o.append( thing_to_append )

    write_file_global_cache_data(a_without_o,       "cache-dataset-normal.js")
    write_file_global_cache_data(a_OC20_IS2RE,      "cache-dataset-OC20_IS2RE.js")
    write_file_global_cache_data(a_OC20_MD,         "cache-dataset-OC20_MD.js")
    write_file_global_cache_data(a_OC20_Rattled,    "cache-dataset-OC20_Rattled.js")
    write_file_global_cache_data(a_OC20_S2EF,       "cache-dataset-OC20_S2EF.js")


def write_file_javascript_cache_data_for_configuration_sets():
    items = cdb.configuration_set_all_nolimit_sortonname()
    a_OC20_IS2RE = []
    a_OC20_MD = []
    a_OC20_Rattled = []
    a_OC20_S2EF = []
    a_without_o = []
    for item in items:
        thing_to_append = [item['colabfit-id'], {'n': item['name'], 'd': item['description']}]
        if item['name'].startswith('IS2RE'):
            a_OC20_IS2RE.append( thing_to_append )

        elif item['name'].startswith('rattled'):
            a_OC20_Rattled.append( thing_to_append )

        elif re.search("OC20 MD", item['description']):
            a_OC20_MD.append( thing_to_append )

        elif re.search("OC20 Train", item['description']):
            a_OC20_S2EF.append( thing_to_append )

        else:
            a_without_o.append( thing_to_append )

    write_file_global_cache_data(a_without_o,       "cache-configuration-set-normal.js")
    write_file_global_cache_data(a_OC20_IS2RE,      "cache-configuration-set-OC20_IS2RE.js")
    write_file_global_cache_data(a_OC20_MD,         "cache-configuration-set-OC20_MD.js")
    write_file_global_cache_data(a_OC20_Rattled,    "cache-configuration-set-OC20_Rattled.js")
    write_file_global_cache_data(a_OC20_S2EF,       "cache-configuration-set-OC20_S2EF.js")


######################################
######################################
##
## __main__
##
######################################
######################################

if __name__ == '__main__':
    runmode = os.environ.get('RUNMODE', '').lower()
    debugmode = True

    if runmode == 'production':
        debugmode = False
    else:
        runmode = 'development'
        debugmode = True
    print( f"Run mode: {runmode}" )

    if( (len(sys.argv) > 1) and sys.argv[1]=="itemcount" ):
        itemcount_dict = {
            'configuration_set_count':      "{:,}".format( cdb.configuration_set_count() ),
            'configuration_count':          "{:,}".format( cdb.configuration_count() ),
            'dataset_count':                "{:,}".format( cdb.dataset_count() ),
            'property_instance_count':      "{:,}".format( cdb.property_instance_count() ),
            'property_definition_count':    "{:,}".format( cdb.property_definition_count() ),
            'metadata_count':               "{:,}".format( cdb.metadata_count() ),
        }
        print("Writing itemcount.json")
        with open("itemcount.json", "w") as outfile:
            print( json.dumps(itemcount_dict, indent=4), file=outfile )
        sys.exit(0)


    if( (len(sys.argv) > 1) and sys.argv[1]=="periodictable" ):
        items = cdb.dataset_all_nolimit()
        a = {}
        for item in items:
            species = []
            for k,v in item['aggregated_info']['total_elements_ratios'].items():
                species.append( k )

            a[ item['colabfit-id'] ] = { #'colabfit-id': item['colabfit-id'],
                                         'e': item['extended-id'],
                                         #'name': item['name'],
                                         's': species }
        print("Writing periodic-table-data.json")
        with open("periodic-table-data.json", "w") as outfile:
            # print( json.dumps(a, indent=4), file=outfile )
            # reduce white space, default separators are (', ', ': ')
            print( json.dumps(a, separators=(',', ':')), file=outfile )
        sys.exit(0)


    if( (len(sys.argv) > 1) and sys.argv[1]=="gencachecs" ):
        write_file_javascript_cache_data_for_configuration_sets()
        sys.exit(0)


    if( (len(sys.argv) > 1) and sys.argv[1]=="gencacheds" ):
        write_file_javascript_cache_data_for_datasets()
        sys.exit(0)

    if not os.path.exists("static/js/cache-dataset-normal.js"):
        write_file_javascript_cache_data_for_configuration_sets()
        write_file_javascript_cache_data_for_datasets()


    # allow world connections
    app.run(host="0.0.0.0", port=4810, debug=debugmode)

    # local only connections
    # app.run(host="localhost", port=4810, debug=debugmode)
