import pymongo
import re
import pprint
from pymongo import MongoClient
import bson.json_util

# 'mongo' resolves to mongo.colabfit.svc.cluster.local
mongo_client = MongoClient('mongo', 27017)
#mongo_client = MongoClient('localhost', 27017)
#mongo_client = MongoClient('localhost', 27017, username="materials_reader", password="materials_reader", authSource='admin')

db = None
for dbname in mongo_client.list_database_names():
    if dbname in [  'cf-update-2023-11-30',
                    #'colabfit-web',
                    #'colabfit',
                    #'colabfit_rebuild_eric',
                    #'colabfit-12-18-22',
                    #'colabfit-2023-5-16',

                    ]:
        db = mongo_client[dbname]
        break

ITEM_SINGULAR_TYPE_TO_COLLECTION = {
    'configuration_set':    db['configuration_sets'],
    'configuration':        db['configurations'],
    'data_object':          db['data_objects'],
    'dataset':              db['datasets'],
    'property_instance':    db['property_instances'],
    'property_definition':  db['property_definitions'],
    'metadata':             db['metadata'],
}

coll_configuration_set = db['configuration_sets']
coll_configuration = db['configurations']
coll_data_object = db['data_objects']
coll_dataset = db['datasets']
coll_property_instance = db['property_instances']
coll_property_definition = db['property_definitions']
coll_metadata = db['metadata']

def demoquerydatasets(
        name=None,
        authors=None,
        description=None,
        doi=None,
        elements=None,
        min_co=None,
        max_co=None,
        min_elements=None,
        max_elements=None,
        min_atoms=None,
        max_atoms=None,
        property_types=None,
        elements_match_only_selected=False,
        given_sort_by=None,
        given_sort_direction='ascending'):

    query = {}
    _internal_sort_by=None
    _internal_sort_direction=None

    if given_sort_direction=='ascending':
        _internal_sort_direction=pymongo.ASCENDING
    else:
        _internal_sort_direction=pymongo.DESCENDING

    match given_sort_by:
        case "nconfigurations":
             _internal_sort_by="aggregated_info.nconfigurations"
        case "nelements":
             _internal_sort_by="aggregated_info.nelements"
        case "nsites":
             _internal_sort_by="aggregated_info.nsites"
        case "colabfit-id":
             _internal_sort_by="colabfit-id"
        case _:
             _internal_sort_by="name"


    ##
    if( min_co and min_co.isnumeric() ):
        min_co = int( min_co )
        k = "aggregated_info.nconfigurations"
        if( not query.get(k) ):
            query[k] = {}
        query[k]["$gte"] = min_co

    if( max_co and max_co.isnumeric() ):
        max_co = int( max_co )
        k = "aggregated_info.nconfigurations"
        if( not query.get(k) ):
            query[k] = {}
        query[k]["$lte"] = max_co

    ##
    if( min_elements and min_elements.isnumeric() ):
        min_elements = int( min_elements )
        k = "aggregated_info.nelements"
        if( not query.get(k) ):
            query[k] = {}
        query[k]["$gte"] = min_elements

    if( max_elements and max_elements.isnumeric() ):
        max_elements = int( max_elements )
        k = "aggregated_info.nelements"
        if( not query.get(k) ):
            query[k] = {}
        query[k]["$lte"] = max_elements

    ##
    if( min_atoms and min_atoms.isnumeric() ):
        min_atoms = int( min_atoms )
        k = "aggregated_info.nsites"
        if( not query.get(k) ):
            query[k] = {}
        query[k]["$gte"] = min_atoms

    if( max_atoms and max_atoms.isnumeric() ):
        max_atoms = int( max_atoms )
        k = "aggregated_info.nsites"
        if( not query.get(k) ):
            query[k] = {}
        query[k]["$lte"] = max_atoms


    if( elements and isinstance(elements, list) ):
        if elements_match_only_selected:
            query["aggregated_info.elements"] = elements
        else:
            query["aggregated_info.elements"] = {"$all":elements}


    if( property_types and isinstance(property_types, list) ):
        query["aggregated_info.property_types"] = {"$all":property_types}

    #add wildcards
    if name:
        name = re.escape(name)
        name = f".*{name}.*"
        query['name'] = {"$regex":name, '$options' : 'i'}

    if authors:
        authors = re.escape(authors)
        authors = f".*{authors}.*"
        query['authors'] = {"$regex":authors, '$options' : 'i'}

    if description:
        description = re.escape(description)
        description = f".*{description}.*"
        query['description'] = {"$regex":description, '$options' : 'i'}

    if doi:
        doi = re.escape(doi)
        doi = f".*{doi}.*"
        query['links'] = {"$regex":doi}


    #query['name'] = {"$regex":name}
    #query['authors'] = {"$regex":authors}
    #query['description'] = {"$regex":description}
    #query['links'] = {"$regex":doi}
    #query["aggregated_info.nconfigurations"] = {"$gt":min_co, "$lt":max_co}
    #query["aggregated_info.nsites"] = {"$gt":min_atoms,"$lt":max_atoms}

    print( query )
    #return coll_dataset.find(query).limit(1000).sort('colabfit-id')
    return coll_dataset.find(query).limit(1000).collation({"locale": "en" }).sort(_internal_sort_by, _internal_sort_direction)



def hello():
    pprint.pprint( db.list_collection_names() )
    coll_configuration_set.find_one()['relationships']

    pprint.pprint(coll_configuration_set.find_one())

    pprint.pprint(coll_configuration_set.find_one({"colabfit-id": "CS_xkf2tdb9ml67_0"}))

    for item in coll_configuration_set.find():
        pprint.pprint( item['colabfit-id'] )

    for item in coll_configuration_set.find( {"colabfit-id": {"$in": ["CS_xkf2tdb9ml67_0"] } } ):
        pprint.pprint( item['colabfit-id'] )

    pprint.pprint( coll_configuration.find_one() )
    pprint.pprint( coll_dataset.find_one() )
    pprint.pprint( coll_property_instance.find_one() )
    pprint.pprint( coll_metadata.find_one() )
    pprint.pprint( coll_property_definition.find_one() )

    for item in coll_property_definition.find():
        pprint.pprint( item['definition']['property-id'] )



"""
get_by_relationship_from_collection('configuration_set', 'dataset', 'ids', 'CS_zodn7xzdzudz_0')
get_by_relationship_from_collection('configuration_set', 'dataset', 'objects', 'CS_zodn7xzdzudz_0')[0]
get_by_relationship_from_collection('configuration_set', 'configuration', 'ids', 'CS_zodn7xzdzudz_0')
get_by_relationship_from_collection('configuration_set', 'configuration', 'objects', 'CS_zodn7xzdzudz_0')[0]


get_by_relationship_from_collection('configuration', 'data_object', 'ids', 'CO_539889399012919435')
get_by_relationship_from_collection('configuration', 'data_object', 'objects', 'CO_539889399012919435')[0]
get_by_relationship_from_collection('configuration', 'dataset', 'ids', 'CO_539889399012919435')
get_by_relationship_from_collection('configuration', 'dataset', 'objects', 'CO_539889399012919435')[0]
get_by_relationship_from_collection('configuration', 'metadata', 'ids', 'CO_539889399012919435')
get_by_relationship_from_collection('configuration', 'metadata', 'objects', 'CO_539889399012919435')[0]
get_by_relationship_from_collection('configuration', 'configuration_set', 'ids', 'CO_539889399012919435')
get_by_relationship_from_collection('configuration', 'configuration_set', 'objects', 'CO_539889399012919435')[0]

get_by_relationship_from_collection('configuration', 'configuration_set', 'ids', 'CO_1519307554759497867')
get_by_relationship_from_collection('configuration', 'configuration_set', 'objects', 'CO_1519307554759497867')[0]


get_by_relationship_from_collection('data_object', 'dataset', 'ids', 'DO_455038150570778675')
get_by_relationship_from_collection('data_object', 'dataset', 'objects', 'DO_455038150570778675')[0]
get_by_relationship_from_collection('data_object', 'configuration', 'ids', 'DO_455038150570778675')
get_by_relationship_from_collection('data_object', 'configuration', 'objects', 'DO_455038150570778675')[0]
get_by_relationship_from_collection('data_object', 'property_instance', 'ids', 'DO_455038150570778675')
get_by_relationship_from_collection('data_object', 'property_instance', 'objects', 'DO_455038150570778675')[0]

DO_589754979400491793

get_by_relationship_from_collection('property_instance', 'dataset', 'ids', 'PI_350473006025884008')
get_by_relationship_from_collection('property_instance', 'dataset', 'objects', 'PI_350473006025884008')[0]
get_by_relationship_from_collection('property_instance', 'data_object', 'ids', 'PI_350473006025884008')
get_by_relationship_from_collection('property_instance', 'data_object', 'objects', 'PI_350473006025884008')[0]
get_by_relationship_from_collection('property_instance', 'metadata', 'ids', 'PI_350473006025884008')
get_by_relationship_from_collection('property_instance', 'metadata', 'objects', 'PI_350473006025884008')[0]

get_by_relationship_from_collection('dataset', 'data_object', 'ids', 'DS_f7q4s8xfng2t_0')
get_by_relationship_from_collection('dataset', 'data_object', 'objects', 'DS_f7q4s8xfng2t_0')[0]
get_by_relationship_from_collection('dataset', 'configuration', 'ids', 'DS_f7q4s8xfng2t_0')
get_by_relationship_from_collection('dataset', 'configuration', 'objects', 'DS_f7q4s8xfng2t_0')[0]
get_by_relationship_from_collection('dataset', 'configuration_set', 'ids', 'DS_f7q4s8xfng2t_0')
get_by_relationship_from_collection('dataset', 'configuration_set', 'objects', 'DS_f7q4s8xfng2t_0')[0]


get_by_relationship_from_collection('metadata', 'property_instance', 'ids', 'MD_1161834823859590840')
get_by_relationship_from_collection('metadata', 'property_instance', 'objects', 'MD_1161834823859590840')[0]
get_by_relationship_from_collection('metadata', 'configuration', 'ids', 'MD_716714805868382596')
get_by_relationship_from_collection('metadata', 'configuration', 'objects', 'MD_716714805868382596')[0]
"""
def get_by_relationship_from_collection(have, want, return_type, short_id, *, find_limit=0):
    if return_type not in ['ids', 'objects']:
        raise Exception("Unkown return_type in get_by_relationship_from_collection")
    want_related_to_have = [
        ['configuration_set',   'dataset',              'in_relationship_of_have'],
        ['configuration_set',   'configuration',        'not_in_relationship_of_have'],
        ['configuration',       'data_object',          'not_in_relationship_of_have'],
        ['configuration',       'dataset',              'in_relationship_of_have'],
        ['configuration',       'configuration_set',    'not_in_relationship_of_have'],
        ['data_object',         'dataset',              'in_relationship_of_have'],
        ['data_object',         'metadata',             'in_relationship_of_have'],
        ['data_object',         'configuration',        'in_relationship_of_have'],
        ['data_object',         'property_instance',    'in_relationship_of_have'],
        ['property_instance',   'dataset',              'in_relationship_of_have'],
        ['property_instance',   'data_object',          'not_in_relationship_of_have'],
        ['dataset',             'data_object',          'not_in_relationship_of_have'],
        ['dataset',             'configuration',        'not_in_relationship_of_have'],
        ['dataset',             'configuration_set',    'not_in_relationship_of_have'],
        ['metadata',            'data_object',          'not_in_relationship_of_have'],
    ]
    if [have, want, 'in_relationship_of_have'] in want_related_to_have:
        if( return_type == 'ids' ):
            collection_have = ITEM_SINGULAR_TYPE_TO_COLLECTION[have]
            one_item = collection_have.find_one({"colabfit-id": short_id})
            arr1 = [x.get(want, None) for x in one_item['relationships']]

            # NOTE: Added 2024-01-10 - Does same update need to be made to objects below?
            # DOs can now have list of lists in relationships
            arr2 = []
            for x in arr1:
                if isinstance(x,list):
                    for y in x:
                        arr2.append(y)
                else:
                    arr2.append(x)

            arr1 = list(filter(None,arr2)) # remove None values
            return arr1

        elif( return_type == 'objects' ):
            collection_have = ITEM_SINGULAR_TYPE_TO_COLLECTION[have]
            one_item = collection_have.find_one({"colabfit-id": short_id})
            arr1 = [x.get(want, None) for x in one_item['relationships']]
            arr1 = list(filter(None,arr1)) # remove None values
            collection_want = ITEM_SINGULAR_TYPE_TO_COLLECTION[want]
            arr2 = collection_want.find( {"colabfit-id": {"$in": arr1 } } ).limit(find_limit).sort('colabfit-id')
            return arr2

    elif [have, want, 'not_in_relationship_of_have'] in want_related_to_have:
        if( return_type == 'ids' ):
            collection_want = ITEM_SINGULAR_TYPE_TO_COLLECTION[want]
            arr1 = collection_want.find({f"relationships.{have}": short_id}, {'colabfit-id':1}).limit(find_limit)
            arr2 = [x['colabfit-id'] for x in arr1]
            return arr2
        elif( return_type == 'objects' ):
            collection_want = ITEM_SINGULAR_TYPE_TO_COLLECTION[want]
            arr1 = collection_want.find({f"relationships.{have}": short_id}).limit(find_limit)
            return arr1
    else:
        raise Exception("Unkown have/want relationship in get_by_relationship_from_collection")


######################################
## configuration_set
######################################

def configuration_set_all():
    return coll_configuration_set.find().limit(1000).sort('colabfit-id')

def configuration_set_all_nolimit():
    return coll_configuration_set.find().sort('colabfit-id')

def configuration_set_all_nolimit_sortonname():
    return coll_configuration_set.find().sort('name')


def configuration_set_count():
    return coll_configuration_set.estimated_document_count()

# CS_zodn7xzdzudz_0
# CS_hux8jirl4lw1_0
def configuration_set_one(short_id):
    return coll_configuration_set.find_one({"colabfit-id": short_id})

###
# Given ConfigurationSet, return related Datasets
#
def configuration_set_relationship_dataset_all_ids(short_id):
    return get_by_relationship_from_collection('configuration_set', 'dataset', 'ids', short_id)

def configuration_set_relationship_dataset_all_objects(short_id):
    return get_by_relationship_from_collection('configuration_set', 'dataset', 'objects', short_id)

###
# Given ConfigurationSet, return related Configurations
#
def configuration_set_relationship_configuration_all_ids(short_id):
    return get_by_relationship_from_collection('configuration_set', 'configuration', 'ids', short_id)

def configuration_set_relationship_configuration_all_objects(short_id):
    return get_by_relationship_from_collection('configuration_set', 'configuration', 'objects', short_id)


######################################
## configuration
######################################

def configuration_all():
    return coll_configuration.find().limit(1000).sort('colabfit-id')

def configuration_count():
    return coll_configuration.estimated_document_count()

# CO_1000000100772348563
def configuration_one(short_id):
    return coll_configuration.find_one({"colabfit-id": short_id})

###
# Given Configuration, return related DataObjects
#
def configuration_relationship_data_object_all_ids(short_id):
    return get_by_relationship_from_collection('configuration', 'data_object', 'ids', short_id)

def configuration_relationship_data_object_all_objects(short_id):
    return get_by_relationship_from_collection('configuration', 'data_object', 'objects', short_id)

###
# Given Configuration, return related Dataset
#
def configuration_relationship_dataset_all_ids(short_id):
    return get_by_relationship_from_collection('configuration', 'dataset', 'ids', short_id)

def configuration_relationship_dataset_all_objects(short_id):
    return get_by_relationship_from_collection('configuration', 'dataset', 'objects', short_id)

###
# Given Configuration, return related ConfigurationSet
#
def configuration_relationship_configuration_set_all_ids(short_id):
    return get_by_relationship_from_collection('configuration', 'configuration_set', 'ids', short_id)

def configuration_relationship_configuration_set_all_objects(short_id):
    return get_by_relationship_from_collection('configuration', 'configuration_set', 'objects', short_id)


######################################
## data_object
######################################

def data_object_all():
    return coll_data_object.find().limit(500).sort('colabfit-id')

def data_object_count():
    return coll_data_object.estimated_document_count()

def data_object_one(short_id):
    return coll_data_object.find_one({"colabfit-id": short_id})

def data_object_relationship_configuration_id(short_id):
    ids = get_by_relationship_from_collection('data_object', 'configuration', 'ids', short_id)
    if len(ids) != 1:
        raise Exception(f"error in data_object_relationship_configuration_id using colabfit-id {short_id}, returned {ids}")
    return ids[0]

def data_object_relationship_dataset_all_ids(short_id):
    return get_by_relationship_from_collection('data_object', 'dataset', 'ids', short_id)

def data_object_relationship_property_instance_all_ids(short_id):
    return get_by_relationship_from_collection('data_object', 'property_instance', 'ids', short_id)

def data_object_relationship_property_instance_all_objects(short_id):
    return get_by_relationship_from_collection('data_object', 'property_instance', 'objects', short_id)

def data_object_relationship_metadata_all_ids(short_id):
    return get_by_relationship_from_collection('data_object', 'metadata', 'ids', short_id)

def data_object_relationship_metadata_all_objects(short_id):
    return get_by_relationship_from_collection('data_object', 'metadata', 'objects', short_id)

######################################
## dataset
######################################

def dataset_all():
    return coll_dataset.find().limit(1000).sort('colabfit-id')

def dataset_all_nolimit():
    return coll_dataset.find().sort('colabfit-id')

def dataset_all_nolimit_sortonname():
    return coll_dataset.find().sort('name')

def dataset_count():
    return coll_dataset.estimated_document_count()

def dataset_last_modified():
    return coll_dataset.find_one({},{'last_modified':1},sort=[('last_modified',-1)])['last_modified']

def dataset_one(short_id):
    return coll_dataset.find_one({"colabfit-id": short_id})

def dataset_relationship_configuration_set_all_ids(short_id):
    return get_by_relationship_from_collection('dataset', 'configuration_set', 'ids', short_id)

def dataset_relationship_configuration_set_all_objects(short_id):
    return get_by_relationship_from_collection('dataset', 'configuration_set', 'objects', short_id)

def dataset_relationship_data_object_all_ids(short_id):
    return get_by_relationship_from_collection('dataset', 'data_object', 'ids', short_id)

def dataset_relationship_data_object_all_ids_with_find_limit(short_id, find_limit):
    return get_by_relationship_from_collection('dataset', 'data_object', 'ids', short_id, find_limit=find_limit)

def dataset_relationship_data_object_count(short_id):
    return db['configurations'].count_documents({f"relationships.dataset": short_id})

def dataset_relationship_data_object_all_objects(short_id):
    return get_by_relationship_from_collection('dataset', 'data_object', 'objects', short_id)


######################################
## property_instance
######################################

def property_instance_all():
    return coll_property_instance.find().limit(500).sort('colabfit-id')

def property_instance_count():
    return coll_property_instance.estimated_document_count()

def property_instance_one(short_id):
    return coll_property_instance.find_one({"colabfit-id": short_id})

#def property_instance_relationship_configuration_all_ids(short_id):
#    return get_by_relationship_from_collection('property_instance', 'configuration', 'ids', short_id)
#
#def property_instance_relationship_configuration_all_objects(short_id):
#    return get_by_relationship_from_collection('property_instance', 'configuration', 'objects', short_id)

def property_instance_relationship_data_object_all_ids(short_id):
    return get_by_relationship_from_collection('property_instance', 'data_object', 'ids', short_id)

def property_instance_relationship_data_object_all_objects(short_id):
    return get_by_relationship_from_collection('property_instance', 'data_object', 'objects', short_id)


######################################
## metadata
######################################

def metadata_all():
    return coll_metadata.find().limit(500).sort('colabfit-id')

def metadata_count():
    return coll_metadata.estimated_document_count()

def metadata_one(short_id):
    return coll_metadata.find_one({"colabfit-id": short_id})

def metadata_relationship_data_object_all_ids(short_id):
    return get_by_relationship_from_collection('metadata', 'data_object', 'ids', short_id)


######################################
## property_definition
######################################

def property_definition_all():
    return coll_property_definition.find().sort('colabfit-id')

def property_definition_count():
    return coll_property_definition.estimated_document_count()

def property_definition_one(property_id):
    return coll_property_definition.find_one({"definition.property-id": property_id})
