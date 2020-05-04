import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 5

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  CORS(app)

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers',
                          'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods',
                          'GET,PUT,POST,DELETE,OPTIONS')
    return response

  @app.route('/categories')
  def retrieve_categories():
    categories = Category.query.order_by(Category.type).all()

    if len(categories) == 0:
        abort(404)

    return jsonify({
      'success': True,
      'categories': [category.type for category in categories],
    })

  @app.route('/questions')
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    categories = Category.query.all()

    if len(current_questions) == 0:
        abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(selection),
      'categories': [category.type for category in categories],
      'current_category': None
    })

  @app.route("/questions/<question_id>", methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.get(question_id)
    if not question:
      abort(422)
    question.delete()
    return jsonify({
      'success': True,
      'deleted': question_id
    })

  @app.route("/questions", methods=['POST'])
  def add_question():
    body = request.get_json()

    if not ('question' in body and 'answer' in body and 'difficulty' in body and 'category' in body):
       abort(422)

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)

    try:
      question = Question(question=new_question, answer=new_answer,
                          difficulty=new_difficulty, category=new_category)
      question.insert()
      return jsonify({
        'success': True,
        'created': question.id,
      })
    except:
      abort(422)

  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    body = request.get_json()
    search_term = body.get('searchTerm', None)

    if not search_term:
      abort(404)

    search_results = Question.query.filter(
      Question.question.ilike(f'%{search_term}%')
    ).all()
    return jsonify({
        'success': True,
        'questions': [question.format() for question in search_results],
        'total_questions': len(search_results),
        'current_category': None
    })

  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def retrieve_questions_by_category(category_id):

    questions = Question.query.filter(
      Question.category == str(category_id+1)
    ).all()

    if len(questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': [question.format() for question in questions],
      'total_questions': len(questions),
      'current_category': category_id+1
    })

  @app.route('/quizzes', methods=['POST'])
  def play_quiz():

    try:
      body = request.get_json()
      if not ('quiz_category' in body and 'previous_questions' in body):
        abort(422)
      category = body.get('quiz_category')
      previous_questions = body.get('previous_questions')

      if category['type'] == 'click':
        new_question = Question.query.filter(
          Question.id.notin_((previous_questions))
        ).all()
      else:
        new_question = Question.query.filter_by(
          category=category['id']
        ).filter(Question.id.notin_((previous_questions))).all()

      return jsonify({
        'success': True,
        'question': random.choice(new_question).format() if new_question else None,
      })
    except:
      abort(422)

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "resource not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "unprocessable"
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "bad request"
    }), 400
  return app
