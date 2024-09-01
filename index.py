import json
import boto3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from boto3.dynamodb.conditions import Attr
from functools import reduce


def get_user_profile(user_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('UserProfile-3ai2clc5pzfchiy2fvaf5iqxwy-dev')
    response = table.get_item(Key={'id': user_id})
    return response.get('Item')


def get_all_products():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('SkinCareProduct-3ai2clc5pzfchiy2fvaf5iqxwy-dev')
    response = table.scan()
    return response.get('Items')


# def get_filtered_products(skin_type, product_type, notable_effects_filter):
#     dynamodb = boto3.resource('dynamodb')
#     table = dynamodb.Table('SkinCareProduct-3ai2clc5pzfchiy2fvaf5iqxwy-dev')
    
#     # Scan with Filter Expressions
#     response = table.scan(
#         FilterExpression=Attr('skintype').contains(skin_type) &
#                          Attr('productType').eq(product_type) &
#                          Attr('notableEffects').contains(notable_effects_filter)
#     )
#     return response.get('Items')


# def get_filtered_products(skin_type, product_type, notable_effects_filter):
#     dynamodb = boto3.resource('dynamodb')
#     table = dynamodb.Table('SkinCareProduct-3ai2clc5pzfchiy2fvaf5iqxwy-dev')
    
#     # Log the filter criteria
#     print(f"Filtering for skin_type: {skin_type}, product_type: {product_type}, notable_effects: {notable_effects_filter}")
    
#     # Scan with Filter Expressions
#     response = table.scan(
#         FilterExpression=Attr('skintype').contains(skin_type) &
#                          Attr('productType').eq(product_type) &
#                          Attr('notableEffects').contains(notable_effects_filter)
#     )
    
#     items = response.get('Items')
    
#     # Log the number of products found
#     print(f"Found {len(items)} products matching the criteria.")
    
#     return items


def get_filtered_products(skin_type, product_type, notable_effects_filter):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('SkinCareProduct-3ai2clc5pzfchiy2fvaf5iqxwy-dev')
    
    # Log the filter criteria
    print(f"Filtering for skin_type: {skin_type}, product_type: {product_type}, notable_effects: {notable_effects_filter}")
    
    # Ensure that notable_effects_filter is treated as a list
    if isinstance(notable_effects_filter, str):
        notable_effects_filter = notable_effects_filter.split()  # Splits by whitespace

    # Define your base filter conditions (skintype and productType)
    filter_expression = (
        Attr('skintype').contains(skin_type) &
        Attr('productType').eq(product_type)
    )
    
    # Perform the initial scan with only the skintype and productType filter
    response = table.scan(
        FilterExpression=filter_expression
    )
    
    # Get the items after the first filter
    items = response.get('Items', [])
    
    # Log the number of products found after the first filter
    print(f"Found {len(items)} products after filtering by skin_type and product_type.")
    
    # Print the first few items to inspect
    for item in items[:5]:
        print(f"Product: {item['productType']}, Notable Effects: {item.get('notableEffects', [])}")
    
    # If notable_effects_filter is not empty, apply the additional filter for notable effects
    if notable_effects_filter:
        filtered_items = []
        for item in items:
            notable_effects = item.get('notableEffects', [])
            print(f"Checking notable effects: {notable_effects} against filters: {notable_effects_filter}")
            if any(effect in notable_effects for effect in notable_effects_filter):
                print(f"Match found: {notable_effects}")
                filtered_items.append(item)
        
        # Log the number of products found after notable effects filtering
        print(f"Found {len(filtered_items)} products after filtering by notable effects.")
        return filtered_items

    # If no notable effects filter is provided, return the items from the initial filter
    return items






# Function to generate product recommendations using TF-IDF and cosine similarity
# def recommend_products(user_profile, filtered_products):
    
#     # Extract user preferences from the profile
#     user_skin_type = user_profile.get('skintype', '')
#     user_notable_effects = user_profile.get('notableEffects', [])
    
#     # Filter products by the user's skin type
#     suitable_products = [p for p in filtered_products if user_skin_type in p.get('skintype', [])]

#     # Prepare product descriptions for TF-IDF
#     product_descriptions = [' '.join(p.get('notableEffects', [])) for p in suitable_products]
    
#     # Initialize TF-IDF vectorizer and calculate the matrix
#     vectorizer = TfidfVectorizer()
#     tfidf_matrix = vectorizer.fit_transform(product_descriptions)
    
#     # Calculate cosine similarity between user preferences and products
#     user_profile_vector = vectorizer.transform([' '.join(user_notable_effects)])
#     cosine_similarities = cosine_similarity(user_profile_vector, tfidf_matrix)
    
#     # Get the top 5 product recommendations
#     top_indices = cosine_similarities.argsort()[0][-5:][::-1]
#     recommendations = [suitable_products[i]['productName'] for i in top_indices]
    
#     # Return the recommended product names
#     return recommendations

def recommend_products(user_profile, products):
    # Extract user preferences from the profile
    user_skin_type = user_profile.get('skintype', '')
    user_notable_effects = user_profile.get('notableEffects', [])
    
    # Filter products by the user's skin type
    suitable_products = [p for p in products if user_skin_type in p.get('skintype', [])]

    # Prepare product descriptions for TF-IDF
    product_descriptions = [' '.join(p.get('notableEffects', [])) for p in suitable_products]
    
    # Check if product_descriptions is empty or contains insufficient data
    if not product_descriptions or all(len(desc.strip()) == 0 for desc in product_descriptions):
        return []  # Return an empty list or handle this case as needed
    
    # Initialize TF-IDF vectorizer and calculate the matrix
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(product_descriptions)
    
    # Calculate cosine similarity between user preferences and products
    user_profile_vector = vectorizer.transform([' '.join(user_notable_effects)])
    cosine_similarities = cosine_similarity(user_profile_vector, tfidf_matrix)
    
    # Get the top 5 product recommendations
    top_indices = cosine_similarities.argsort()[0][-5:][::-1]
    recommendations = [suitable_products[i]['productName'] for i in top_indices]
    
    # Return the recommended product names
    return recommendations




def update_user_profile(user_id, recommendations):
   
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    
    # Reference the UserProfile table
    table = dynamodb.Table('UserProfile-3ai2clc5pzfchiy2fvaf5iqxwy-dev')
    
    # Update the user's profile with the list of recommended products
    table.update_item(
        Key={'id': user_id},
        UpdateExpression="set recommendedProducts = :r",
        ExpressionAttributeValues={':r': recommendations}
    )




# This Lambda function processes an HTTP request to generate and return product recommendations for a user:

# It extracts the user's email from the request.
# Retrieves the user's profile from DynamoDB.
# Filters products based on the user's preferences.
# Generates product recommendations.
# Updates the user's profile with these recommendations.
# Returns the recommendations as a JSON response.
# Main Lambda handler function
# def handler(event, context):
#     # Extract the user's email from the event data
#     user_email = event['queryStringParameters']['email']
    
#     # Fetch the user's profile from DynamoDB
#     user_profile = get_user_profile(user_email)
    
#     # Extract relevant user information for filtering products
#     skin_type = user_profile.get('skintype', '')
#     product_type = user_profile.get('productType', '')
#     notable_effects = user_profile.get('notableEffects', [])
    
#     # Fetch the products filtered by the user's preferences
#     products = get_filtered_products(skin_type, product_type, ' '.join(notable_effects))
    
#     # Generate product recommendations based on the user's profile
#     recommendations = recommend_products(user_profile, products)
    
#     # Update the user's profile in DynamoDB with the recommendations
#     update_user_profile(user_email, recommendations)
    
#     # Return a successful response with the recommendations
#     return {
#         'statusCode': 200,
#         'headers': {
#             'Access-Control-Allow-Headers': '*',
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
#         },
#         'body': json.dumps({'recommendations': recommendations})
#     }


# def handler(event, context):
#     # Extract id from event (assuming it's directly provided)
#     user_id = event['arguments']['id']  # Change to the correct path based on your event structure
    
#     # Retrieve the user profile by id
#     user_profile = get_user_profile(user_id)
#     if not user_profile:
#         return {
#             'statusCode': 404,
#             'body': json.dumps({'error': 'User not found'})
#         }
    
#     # Now proceed with filtering and recommendations
#     skin_type = user_profile.get('skintype', '')
#     product_type = user_profile.get('productType', '')
#     notable_effects = user_profile.get('notableEffects', [])
    
#     products = get_filtered_products(skin_type, product_type, ' '.join(notable_effects))
#     recommendations = recommend_products(user_profile, products)
    
#     update_user_profile(user_id, recommendations)
    
#     return {
#         'statusCode': 200,
#         'headers': {
#             'Access-Control-Allow-Headers': '*',
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
#         },
#         'body': json.dumps({'recommendations': recommendations})
#     }

def handler(event, context):
    # Extract id from event (assuming it's directly provided)
    user_id = event['arguments']['id']  # Correctly using 'arguments' instead of 'queryStringParameters'
    
    # Retrieve the user profile by id
    user_profile = get_user_profile(user_id)
    if not user_profile:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'User not found'})
        }
    
    # Proceed with filtering and recommendations
    skin_type = user_profile.get('skintype', '')
    product_type = user_profile.get('productType', '')
    notable_effects = user_profile.get('notableEffects', [])
    
    products = get_filtered_products(skin_type, product_type, ' '.join(notable_effects))
    recommendations = recommend_products(user_profile, products)
    
    update_user_profile(user_id, recommendations)
    
    # Return only the recommendations list
    return recommendations