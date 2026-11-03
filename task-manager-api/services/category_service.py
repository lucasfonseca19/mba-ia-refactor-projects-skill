from database import db
from models.category import Category


class CategoryInputError(ValueError):
    pass


def apply_data(category, data, create=False):
    if not isinstance(data, dict) or not data:
        raise CategoryInputError('Dados inválidos')
    if create and ('name' not in data or not data['name']):
        raise CategoryInputError('Nome é obrigatório')
    for key in ('name', 'description', 'color'):
        if key in data:
            if (data[key] is None and key == 'name') or (data[key] is not None and not isinstance(data[key], str)) or (key == 'name' and not data[key]):
                raise CategoryInputError('Dados inválidos')
            setattr(category, key, data[key])
    if create:
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')
    return category


def find_category(category_id):
    return db.session.get(Category, category_id)


def create_category(data):
    category = apply_data(Category(), data, create=True)
    db.session.add(category)
    db.session.commit()
    return category


def update_category(category, data):
    apply_data(category, data)
    db.session.commit()
    return category


def delete_category(category):
    db.session.delete(category)
    db.session.commit()
