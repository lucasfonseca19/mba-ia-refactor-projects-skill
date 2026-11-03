"""Mapa dos 19 contratos originais e suas políticas de acesso."""
from controllers import products,users,orders,system
from security import login_required


def register_routes(app):
    routes = [
        ("GET","/",system.index,"public"),
        ("GET","/health",system.health,"public"),
        ("GET","/produtos",products.list_products,"public"),
        ("GET","/produtos/busca",products.search_products,"public"),
        ("GET","/produtos/<int:id>",products.get_product,"public"),
        ("POST","/produtos",products.create_product,"admin"),
        ("PUT","/produtos/<int:id>",products.update_product,"admin"),
        ("DELETE","/produtos/<int:id>",products.delete_product,"admin"),
        ("GET","/usuarios",users.list_users,"admin"),
        ("GET","/usuarios/<int:id>",users.get_user,"authenticated"),
        ("POST","/usuarios",users.create_user,"public"),
        ("POST","/login",users.login,"public"),
        ("POST","/pedidos",orders.create_order,"authenticated"),
        ("GET","/pedidos",orders.list_orders,"admin"),
        ("GET","/pedidos/usuario/<int:usuario_id>",orders.user_orders,"authenticated"),
        ("PUT","/pedidos/<int:pedido_id>/status",orders.update_status,"admin"),
        ("GET","/relatorios/vendas",system.sales_report,"admin"),
        ("POST","/admin/reset-db",system.reset_database,"admin"),
        ("POST","/admin/query",system.execute_query,"admin"),
    ]
    for method,path,handler,access in routes:
        view = handler if access == "public" else login_required(admin=access=="admin")(handler)
        app.add_url_rule(path,endpoint=f"{handler.__module__}.{handler.__name__}",view_func=view,methods=[method])
