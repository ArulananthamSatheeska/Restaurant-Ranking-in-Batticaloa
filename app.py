from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
import pickle
import nltk
from nltk.tokenize import word_tokenize

# Ensure NLTK punkt is downloaded
nltk.download('punkt')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key for session management

# Load custom stopwords
def read_lines(filename):
    with open(filename, 'r', encoding="utf-8") as fp:
        return [line.strip().lower() for line in fp.readlines()]

stop_words = read_lines("emotion/stopwords/stopwords.txt")

def cutword(x):
    seg = word_tokenize(x)
    new_seg = [key for key in seg if key.strip().lower() not in stop_words and len(key.strip()) > 1]
    return new_seg

def single_review_sentiment_score(content):
    if not content:
        return 0

    if not isinstance(content, str) or not content.strip():
        return 0
        
    pos_count = sum(1 for word in cutword(content) if word in read_lines("emotion/postive/positive.txt"))
    neg_count = sum(1 for word in cutword(content) if word in read_lines("emotion/negative/negative.txt"))

    return pos_count - neg_count

# Load the model
def load_model(filename='restaurant_model.pkl'):
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    return []

# Function to analyze reviews
def analyze_reviews(reviews):
    pos_count = sum(1 for review in reviews if single_review_sentiment_score(review) > 0)
    neg_count = sum(1 for review in reviews if single_review_sentiment_score(review) < 0)
    total = pos_count + neg_count

    pos_percentage = round(pos_count / total * 100, 2) if total > 0 else 0.0
    neg_percentage = round(neg_count / total * 100, 2) if total > 0 else 0.0

    return {
        'pos_number': pos_count,
        'neg_number': neg_count,
        'pos_percentage': pos_percentage,
        'neg_percentage': neg_percentage
    }

def update_restaurant_data(restaurant_name, new_review, new_recommended_dish, restaurant_results):
    restaurant = next((r for r in restaurant_results if r['name'] == restaurant_name), None)
    
    if restaurant:
        try:
            # Load existing reviews from the Excel file
            df = pd.read_excel(restaurant['file_name'])
            # Calculate the sentiment score of the new review
            score = single_review_sentiment_score(new_review)
            sentiment = 1 if score > 0 else -1  # Only consider positive if score is greater than zero
            
            # Create a new DataFrame row for the new review
            new_row = pd.DataFrame({
                "Review": [new_review],
                "Recommended dishes": [new_recommended_dish],
                "Sentiment": [sentiment]
            })
            # Append the new review to the DataFrame
            df = pd.concat([df, new_row], ignore_index=True)
            # Save the updated DataFrame back to Excel
            df.to_excel(restaurant['file_name'], index=False)

            # Re-analyze all reviews to update restaurant results
            restaurant['result'] = analyze_reviews(df['Review'].tolist())
            restaurant['best_dish'] = new_recommended_dish

        except PermissionError:
            return f"Permission denied: Unable to write to '{restaurant['file_name']}'. Please close the file if it is open and try again."
        except Exception as e:
            return f"An error occurred: {str(e)}"

def get_rankings(restaurant_results):
    # Sort restaurants by positive sentiment percentage
    sorted_restaurants = sorted(restaurant_results, key=lambda x: x['result']['pos_percentage'], reverse=True)
    return sorted_restaurants

@app.route('/')
def index():
    restaurant_results = load_model()
    if restaurant_results is None:
        flash("No restaurant data found. Please ensure the model is saved.")
        return render_template('index.html', restaurants=[])

    return render_template('index.html', restaurants=restaurant_results)

@app.route('/submit', methods=['POST'])
def submit_review():
    restaurant_results = load_model()
    restaurant_name = request.form['restaurant_name']
    new_review = request.form['new_review']
    new_recommended_dish = request.form['new_recommended_dish']

    # Update restaurant data and handle any errors
    error_message = update_restaurant_data(restaurant_name, new_review, new_recommended_dish, restaurant_results)
    
    if error_message:
        flash(error_message)
    else:
        flash(f"Updated data for {restaurant_name}!")

    # Re-rank the restaurants after adding a new review
    sorted_restaurants = get_rankings(restaurant_results)

    return redirect(url_for('index'))

@app.route('/rankings')
def rankings():
    restaurant_results = load_model()
    if restaurant_results is None:
        flash("No restaurant data found. Please ensure the model is saved.")
        return redirect(url_for('index'))
    
    # Get sorted rankings based on positive sentiment percentage
    sorted_restaurants = get_rankings(restaurant_results)
    return render_template('ranking.html', sorted_restaurants=sorted_restaurants)

if __name__ == '__main__':
    app.run(debug=True)
