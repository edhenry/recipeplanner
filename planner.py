import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import openai
from collections import defaultdict

# Correct scopes for Google Sheets and Drive API
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Google Sheets connection
def connect_to_gsheet():
    service_account_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open("Weekly_Dinner_Planner")  # Replace with your Google Sheet name
    return sheet

# Load recipes from Google Sheet
def load_recipes(sheet):
    worksheet = sheet.worksheet("Recipe Database")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Load Ingredients Database from Google Sheet
def load_ingredients_database(sheet):
    worksheet = sheet.worksheet("Ingredients Database")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Scale ingredients based on servings
def scale_ingredients(ingredients_db, meal_name, servings, original_servings):
    ingredients = ingredients_db[ingredients_db["Meal Name"] == meal_name]
    if original_servings == 0:
        return ingredients
    ingredients["Quantity"] = ingredients["Quantity"] * (servings / original_servings)
    return ingredients

# Chat interface with Streamlit's chat elements
def chat_interface_with_streamlit_chat(recipes, ingredients_db):
    st.title("Recipe Assistant")
    st.markdown("### Ask me anything about your meal planning and recipes!")

    # Initialize OpenAI client
    openai.api_key = st.secrets["openai_api_key"]

    # Initialize session state for OpenAI model and messages
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if user_input := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Prepare prompt with context (recipes and user input)
        relevant_recipes = recipes.sample(3)  # Default to 3 random recipes for simplicity
        formatted_recipes = "\n".join([
            f"Recipe: {recipe['Meal Name']}\nCuisine: {recipe['Cuisine']}\nPrep Time: {recipe['Prep Time']} minutes\nIngredients: {recipe['Ingredients']}\nInstructions: {recipe['Instructions']}"
            for _, recipe in relevant_recipes.iterrows()
        ])
        context_prompt = f"""
        You are a recipe assistant. Here are some recipes to help answer user questions:

        {formatted_recipes}

        User Query: {user_input}

        Respond to the user query using the provided recipes.
        """

        # Call OpenAI API with streaming
        with st.chat_message("assistant"):
            stream = openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": "system", "content": "You are a helpful recipe assistant."},
                    *st.session_state.messages,
                    {"role": "user", "content": context_prompt},
                ],
                stream=True,
            )
            response = ""
            for chunk in stream:
                chunk_content = chunk["choices"][0].get("delta", {}).get("content", "")
                response += chunk_content
                st.markdown(chunk_content, unsafe_allow_html=True)
        
        # Save assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})

# Main app
sheet = connect_to_gsheet()
st.sidebar.title("Navigation")
st.sidebar.info(
    """
    **Welcome to the Weekly Dinner Planner!**

    - **Recipe Planner**: Plan your weekly meals and generate a grocery list.
    - **Add Recipes**: Add new recipes with ingredients to your database.
    - **Browse Recipes**: View and scale recipes with ingredients.
    - **Chat Assistant**: Ask questions or get suggestions using a conversational interface.
    """
)
page = st.sidebar.radio("Go to", ["Recipe Planner", "Add Recipes", "Browse Recipes", "Chat Assistant"])

if page == "Recipe Planner":
    st.title("Weekly Recipe Planner")
    st.markdown(
        """
        ### How to Use the Recipe Planner
        1. Use the filters in the sidebar to narrow down recipes.
        2. Assign recipes to each day of the week.
        3. Click **"Generate Grocery List"** to create your shopping list.
        """
    )
    recipes = load_recipes(sheet)
    ingredients_db = load_ingredients_database(sheet)
    # Add planner code here...

elif page == "Add Recipes":
    st.title("Add a New Recipe")
    st.markdown(
        """
        ### How to Add a Recipe
        1. Fill out recipe details.
        2. Add ingredients with quantities and units.
        3. Click **"Add Recipe"** to save it.
        """
    )
    # Add recipe form code here...

elif page == "Browse Recipes":
    st.title("Browse Recipes")
    recipes = load_recipes(sheet)
    ingredients_db = load_ingredients_database(sheet)
    # Add browse recipe code here...

elif page == "Chat Assistant":
    recipes = load_recipes(sheet)
    ingredients_db = load_ingredients_database(sheet)
    chat_interface_with_streamlit_chat(recipes, ingredients_db)