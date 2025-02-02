"""
Pipedrive api docs: https://developers.pipedrive.com/docs/api/v1

Pipedrive changes or deprecates fields and endpoints without versioning the api.
If something breaks, it's a good idea to check the changelog.
Api changelog: https://developers.pipedrive.com/changelog

To get an api key: https://pipedrive.readme.io/docs/how-to-find-the-api-token
"""

import dlt
import requests


@dlt.source(name="pipedrive")
def pipedrive_source(pipedrive_api_key=dlt.secrets.value):
    """

    Args:
    pipedrive_api_key: https://pipedrive.readme.io/docs/how-to-find-the-api-token

    Returns resources:
        activityFields
        dealFields
        deals
        deals_flow
        deals_participants
        organizationFields
        organizations
        personFields
        persons
        pipelines
        productFields
        products
        stages
        users

    Resources that depend on another resource are implemented as tranformers
    so they can re-use the original resource data without re-downloading.
    Examples:  deals_participants, deals_flow

    """

    endpoints = ['persons', 'stages', 'productFields', 'products', 'pipelines', 'personFields',
                 'users', 'organizations', 'organizationFields', 'activityFields', 'dealFields']

    endpoint_resources = [dlt.resource(_get_endpoint(endpoint, pipedrive_api_key), name=endpoint, write_disposition="replace") for endpoint in endpoints]
    # add activities
    activities_resource = dlt.resource(_get_endpoint('activities', pipedrive_api_key, extra_params={'user_id': 0}), name='activities', write_disposition="replace")
    endpoint_resources.append(activities_resource)
    # add resources that need 2 requests

    # we make the resource explicitly and put it in a variable
    deals = dlt.resource(_get_endpoint('deals', pipedrive_api_key), name="deals")

    endpoint_resources.append(deals)

    # in order to avoid calling the deal endpoint 3 times (once for deal, twice for deal_entity)
    # we use a transformer instead of a resource.
    # The transformer can use the deals resource from cache instead of having to get the data again.
    # We use the pipe operator to pass the deals to

    endpoint_resources.append(deals | deals_participants(pipedrive_api_key=pipedrive_api_key))
    endpoint_resources.append(deals | deals_flow(pipedrive_api_key=pipedrive_api_key))
    return endpoint_resources


def _paginated_get(url, headers, params):
    """
    Requests and yields data 500 records at a time
    Documentation: https://pipedrive.readme.io/docs/core-api-concepts-pagination
    """
    # pagination start and page limit
    is_next_page = True
    params['start'] = 0
    params['limit'] = 500
    while is_next_page:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        page = response.json()
        # yield data only
        data = page['data']
        if data:
            yield data
        # check if next page exists
        pagination_info = page.get("additional_data", {}).get("pagination", {})
        # is_next_page is set to True or False
        is_next_page = pagination_info.get("more_items_in_collection", False)
        if is_next_page:
            params['start'] = pagination_info.get("next_start")


def _get_endpoint(entity, pipedrive_api_key, extra_params=None):
    """
    Generic method to retrieve endpoint data based on the required headers and params.

    Args:
        entity: the endpoint you want to call
        pipedrive_api_key:
        extra_params: any needed request params except pagination.

    Returns:

    """
    headers = {"Content-Type": "application/json"}
    params = {'api_token': pipedrive_api_key}
    if extra_params:
        params.update(extra_params)
    url = f'https://app.pipedrive.com/v1/{entity}'
    pages = _paginated_get(url, headers=headers, params=params)
    yield from pages


@dlt.transformer(write_disposition="replace")
def deals_participants(deals_page, pipedrive_api_key=dlt.secrets.value):
    """
    This transformer builds on deals resource data.
    The data is passed to it page by page (as the upstream resource returns it)
    """
    for row in deals_page:
        endpoint = f"deals/{row['id']}/participants"
        data = _get_endpoint(endpoint, pipedrive_api_key)
        if data:
            yield from data


@dlt.transformer(write_disposition="replace")
def deals_flow(deals_page, pipedrive_api_key=dlt.secrets.value):
    """
    This transformer builds on deals resource data.
    The data is passed to it page by page (as the upstream resource returns it)
    """
    for row in deals_page:
        endpoint = f"deals/{row['id']}/flow"
        data = _get_endpoint(endpoint, pipedrive_api_key)
        if data:
            yield from data

if __name__=='__main__':
    # configure the pipeline with your destination details
    pipeline = dlt.pipeline(pipeline_name='pipedrive', destination='bigquery', dataset_name='pipedrive')

    #data = list(deals_participants())
    #print(data)
    # run the pipeline with your parameters
    load_info = pipeline.run(pipedrive_source())

    # pretty print the information on data that was loaded
    print(load_info)
