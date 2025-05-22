"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite

#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/people', methods=['GET'])
def get_all_people():
    people = People.query.all()
    serialized_people = [p.serialize() for p in people]
    return jsonify(serialized_people), 200


@app.route('/people/<int:people_id>', methods=['GET'])
def get_single_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"msg": "Personaje no encontrado"}), 404
    return jsonify(person.serialize()), 200


@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    serialized_planets = [p.serialize() for p in planets]
    return jsonify(serialized_planets), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "Planeta no encontrado"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    serialized_users = [u.serialize() for u in users]
    return jsonify(serialized_users), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():

    user_id = request.args.get('user_id', 1) #
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": f"Usuario con ID {user_id} no encontrado"}), 404

    favorites = Favorite.query.filter_by(user_id=user.id).all()
    serialized_favorites = [f.serialize() for f in favorites]
    return jsonify(serialized_favorites), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
 
    user_id = request.json.get('user_id', 1) 

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": f"Usuario con ID {user_id} no encontrado"}), 404

    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"msg": "Planeta no encontrado"}), 404

 
    existing_favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing_favorite:
        return jsonify({"msg": "El planeta ya está en favoritos"}), 409 

    new_favorite = Favorite(user_id=user_id, planet_id=planet_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify({"msg": "Planeta añadido a favoritos", "favorite": new_favorite.serialize()}), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
 
    user_id = request.json.get('user_id', 1) 

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": f"Usuario con ID {user_id} no encontrado"}), 404

    person = People.query.get(people_id)
    if not person:
        return jsonify({"msg": "Personaje no encontrado"}), 404

    existing_favorite = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
    if existing_favorite:
        return jsonify({"msg": "El personaje ya está en favoritos"}), 409 

    new_favorite = Favorite(user_id=user_id, people_id=people_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify({"msg": "Personaje añadido a favoritos", "favorite": new_favorite.serialize()}), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):

    user_id = request.json.get('user_id', 1)

    favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({"msg": "Planeta favorito no encontrado para este usuario"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Planeta favorito eliminado"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):

    user_id = request.json.get('user_id', 1)

    favorite = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
    if not favorite:
        return jsonify({"msg": "Personaje favorito no encontrado para este usuario"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Personaje favorito eliminado"}), 200




@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    if not data:
        return jsonify({"msg": "Cuerpo de solicitud JSON inválido"}), 400

    email = data.get('email')
    password = data.get('password')
    is_active = data.get('is_active', True) 

    if not email or not password:
        return jsonify({"msg": "Se requiere email y password"}), 400

 
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"msg": "El email ya está registrado"}), 409 

    new_user = User(email=email, password=password, is_active=is_active)
    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify({"msg": "Usuario creado exitosamente", "user": new_user.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error al crear usuario", "error": str(e)}), 500


@app.route('/people', methods=['POST'])
def create_person():
    data = request.json
    if not data:
        return jsonify({"msg": "Cuerpo de solicitud JSON inválido"}), 400

    name = data.get('name')
    if not name:
        return jsonify({"msg": "Se requiere el nombre del personaje"}), 400

    new_person = People(
        name=name,
        height=data.get('height', 'unknown'),
        mass=data.get('mass', 'unknown'),
        hair_color=data.get('hair_color', 'unknown'),
        skin_color=data.get('skin_color', 'unknown'),
        eye_color=data.get('eye_color', 'unknown'),
        birth_year=data.get('birth_year', 'unknown'),
        gender=data.get('gender', 'unknown')
    )
    db.session.add(new_person)
    try:
        db.session.commit()
        return jsonify({"msg": "Personaje creado exitosamente", "person": new_person.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error al crear personaje", "error": str(e)}), 500


@app.route('/planet', methods=['POST'])
def create_planet():
    data = request.json
    if not data:
        return jsonify({"msg": "Cuerpo de solicitud JSON inválido"}), 400

    name = data.get('name')
    if not name:
        return jsonify({"msg": "Se requiere el nombre del planeta"}), 400

    new_planet = Planet(
        name=name,
        climate=data.get('climate', 'unknown'),
        population=data.get('population', 'unknown'),
        orbital_period=data.get('orbital_period', 'unknown'),
        rotation_period=data.get('rotation_period', 'unknown'),
        diameter=data.get('diameter', 'unknown')
    )
    db.session.add(new_planet)
    try:
        db.session.commit()
        return jsonify({"msg": "Planeta creado exitosamente", "planet": new_planet.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error al crear planeta", "error": str(e)}), 500


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
