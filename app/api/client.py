from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import Product, Order, Customer, OrderItem, SecurityIncident
from app.db.models import OrderStatus, PaymentMethod, PaymentStatus
from app.services.notification_service import queue_notification

router = APIRouter()

# Endpoints para el panel de administración web

@router.get("/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales para el dashboard.
    """
    try:
        # Obtener estadísticas de ventas
        total_customers = db.query(Customer).count()
        total_orders = db.query(Order).count()
        
        # Calcular ventas completadas
        completed_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED.value).all()
        total_sales = sum(order.total_amount for order in completed_orders)
        
        # Ventas del día
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_orders = db.query(Order).filter(
            Order.status == OrderStatus.COMPLETED.value,
            Order.created_at.between(today_start, today_end)
        ).all()
        today_sales = sum(order.total_amount for order in today_orders)
        
        # Clientes nuevos hoy
        new_customers = db.query(Customer).filter(
            Customer.created_at.between(today_start, today_end)
        ).count()
        
        # Órdenes pendientes
        pending_orders = db.query(Order).filter(
            Order.status == OrderStatus.PENDING.value
        ).count()
        
        # Top 5 productos más vendidos
        top_products_query = db.query(
            Product.name, 
            Product.id,
            Product.price,
            db.func.sum(OrderItem.quantity).label('total_sold')
        ).join(OrderItem).join(Order).filter(
            Order.status == OrderStatus.COMPLETED.value
        ).group_by(Product.id).order_by(db.func.sum(OrderItem.quantity).desc()).limit(5).all()
        
        top_products = []
        for product in top_products_query:
            top_products.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "total_sold": product.total_sold
            })
        
        # Incidentes de seguridad recientes
        recent_incidents = db.query(SecurityIncident).order_by(
            SecurityIncident.timestamp.desc()
        ).limit(5).all()
        
        incidents = []
        for incident in recent_incidents:
            incidents.append({
                "id": incident.id,
                "type": incident.type,
                "severity": incident.severity,
                "phone_number": incident.phone_number,
                "is_resolved": incident.is_resolved,
                "timestamp": incident.timestamp.isoformat() if incident.timestamp else None
            })
        
        return {
            "total_customers": total_customers,
            "total_orders": total_orders,
            "total_sales": total_sales,
            "today_sales": today_sales,
            "new_customers": new_customers,
            "pending_orders": pending_orders,
            "top_products": top_products,
            "recent_incidents": incidents
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@router.get("/products", response_model=List[Dict[str, Any]])
async def get_products(
    active_only: bool = Query(True, description="Mostrar solo productos activos"),
    skip: int = Query(0, description="Registros a saltar para paginación"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de productos con filtros y paginación.
    """
    try:
        query = db.query(Product)
        
        if active_only:
            query = query.filter(Product.is_active == True)
            
        products = query.offset(skip).limit(limit).all()
        
        result = []
        for product in products:
            result.append({
                "id": product.id,
                "code": product.code,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "image_url": product.image_url,
                "is_active": product.is_active,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            })
            
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")

@router.get("/orders", response_model=List[Dict[str, Any]])
async def get_orders(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    payment_method: Optional[str] = Query(None, description="Filtrar por método de pago"),
    date_from: Optional[str] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    skip: int = Query(0, description="Registros a saltar para paginación"),
    limit: int = Query(50, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de órdenes con filtros y paginación.
    """
    try:
        query = db.query(Order)
        
        # Aplicar filtros
        if status:
            query = query.filter(Order.status == status)
            
        if payment_method:
            query = query.filter(Order.payment_method == payment_method)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Order.created_at >= date_from_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_desde inválido. Use YYYY-MM-DD")
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                date_to_obj = datetime.combine(date_to_obj, datetime.max.time())  # Fin del día
                query = query.filter(Order.created_at <= date_to_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_hasta inválido. Use YYYY-MM-DD")
        
        # Ordenar y paginar
        orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for order in orders:
            # Obtener datos del cliente
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
            
            # Obtener items de la orden
            items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            order_items = []
            
            for item in items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                order_items.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": product.name if product else "Producto no encontrado",
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal
                })
            
            result.append({
                "id": order.id,
                "customer": {
                    "id": customer.id if customer else None,
                    "name": customer.name if customer else "Cliente no encontrado",
                    "phone_number": customer.phone_number if customer else None
                },
                "total_amount": order.total_amount,
                "status": order.status,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "items": order_items
            })
            
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo órdenes: {str(e)}")

@router.get("/customers", response_model=List[Dict[str, Any]])
async def get_customers(
    search: Optional[str] = Query(None, description="Buscar por nombre o teléfono"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    skip: int = Query(0, description="Registros a saltar para paginación"),
    limit: int = Query(50, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de clientes con filtros y paginación.
    """
    try:
        query = db.query(Customer)
        
        # Aplicar filtros
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Customer.name.ilike(search_term),
                    Customer.phone_number.ilike(search_term)
                )
            )
            
        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)
        
        # Ordenar y paginar
        customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for customer in customers:
            # Obtener estadísticas del cliente
            orders_count = db.query(Order).filter(Order.customer_id == customer.id).count()
            
            completed_orders = db.query(Order).filter(
                Order.customer_id == customer.id,
                Order.status == OrderStatus.COMPLETED.value
            ).all()
            
            lifetime_value = sum(order.total_amount for order in completed_orders)
            
            # Obtener última orden
            last_order = db.query(Order).filter(
                Order.customer_id == customer.id
            ).order_by(Order.created_at.desc()).first()
            
            result.append({
                "id": customer.id,
                "name": customer.name,
                "phone_number": customer.phone_number,
                "email": customer.email,
                "address": customer.address,
                "is_active": customer.is_active,
                "is_blocked": customer.is_blocked,
                "created_at": customer.created_at.isoformat() if customer.created_at else None,
                "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
                "stats": {
                    "orders_count": orders_count,
                    "lifetime_value": lifetime_value,
                    "last_order_date": last_order.created_at.isoformat() if last_order else None,
                    "last_order_status": last_order.status if last_order else None
                }
            })
            
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes: {str(e)}")

@router.get("/security/incidents", response_model=List[Dict[str, Any]])
async def get_security_incidents(
    severity: Optional[str] = Query(None, description="Filtrar por severidad"),
    type: Optional[str] = Query(None, description="Filtrar por tipo"),
    is_resolved: Optional[bool] = Query(None, description="Filtrar por resuelto/pendiente"),
    date_from: Optional[str] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    skip: int = Query(0, description="Registros a saltar para paginación"),
    limit: int = Query(50, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de incidentes de seguridad con filtros y paginación.
    """
    try:
        query = db.query(SecurityIncident)
        
        # Aplicar filtros
        if severity:
            query = query.filter(SecurityIncident.severity == severity)
            
        if type:
            query = query.filter(SecurityIncident.type == type)
            
        if is_resolved is not None:
            query = query.filter(SecurityIncident.is_resolved == is_resolved)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(SecurityIncident.timestamp >= date_from_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_desde inválido. Use YYYY-MM-DD")
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                date_to_obj = datetime.combine(date_to_obj, datetime.max.time())  # Fin del día
                query = query.filter(SecurityIncident.timestamp <= date_to_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_hasta inválido. Use YYYY-MM-DD")
        
        # Ordenar y paginar
        incidents = query.order_by(SecurityIncident.timestamp.desc()).offset(skip).limit(limit).all()
        
        result = []
        for incident in incidents:
            # Obtener información del cliente si existe
            customer = None
            if incident.customer_id:
                customer = db.query(Customer).filter(Customer.id == incident.customer_id).first()
            
            result.append({
                "id": incident.id,
                "type": incident.type,
                "description": incident.description,
                "severity": incident.severity,
                "phone_number": incident.phone_number,
                "ip_address": incident.ip_address,
                "message_content": incident.message_content,
                "confidence_score": incident.confidence_score,
                "is_resolved": incident.is_resolved,
                "resolution_notes": incident.resolution_notes,
                "timestamp": incident.timestamp.isoformat() if incident.timestamp else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "phone_number": customer.phone_number
                } if customer else None
            })
            
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo incidentes: {str(e)}")

@router.put("/orders/{order_id}/status", response_model=Dict[str, Any])
async def update_order_status(
    order_id: int = Path(..., description="ID de la orden"),
    status: str = Query(..., description="Nuevo estado de la orden"),
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de una orden.
    """
    try:
        # Verificar estado válido
        try:
            new_status = OrderStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in OrderStatus]
            raise HTTPException(
                status_code=400, 
                detail=f"Estado no válido. Use uno de: {', '.join(valid_statuses)}"
            )
        
        # Buscar la orden
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Orden con ID {order_id} no encontrada")
        
        # Buscar cliente para notificación
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        
        # Actualizar estado
        old_status = order.status
        order.status = new_status.value
        order.updated_at = datetime.now()
        
        # Si se completó el pago, actualizar fecha de pago
        if new_status == OrderStatus.PAID and order.payment_status != PaymentStatus.COMPLETED.value:
            order.payment_status = PaymentStatus.COMPLETED.value
            order.payment_date = datetime.now()
        
        db.commit()
        
        # Enviar notificación al cliente si cambió a un estado relevante
        if customer and customer.phone_number:
            status_messages = {
                OrderStatus.PROCESSING.value: "Tu pedido está siendo procesado",
                OrderStatus.SHIPPED.value: "Tu pedido ha sido enviado",
                OrderStatus.DELIVERED.value: "Tu pedido ha sido entregado",
                OrderStatus.CANCELLED.value: "Tu pedido ha sido cancelado"
            }
            
            if new_status.value in status_messages:
                # Encolar notificación para el cliente
                queue_notification(
                    to=customer.phone_number,
                    message=f"Actualización de tu pedido #{order.id}",
                    channel="whatsapp",
                    template="order_status_update.txt",
                    context={
                        "customer_name": customer.name,
                        "order_id": order.id,
                        "old_status": old_status,
                        "new_status": new_status.value,
                        "status_message": status_messages[new_status.value],
                        "updated_at": datetime.now().isoformat()
                    }
                )
        
        return {
            "success": True,
            "order_id": order.id,
            "old_status": old_status,
            "new_status": order.status,
            "message": f"Estado de la orden actualizado a: {order.status}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando estado: {str(e)}")

@router.post("/security/incidents/{incident_id}/resolve", response_model=Dict[str, Any])
async def resolve_security_incident(
    incident_id: int = Path(..., description="ID del incidente"),
    notes: str = Query(None, description="Notas de resolución"),
    db: Session = Depends(get_db)
):
    """
    Marca un incidente de seguridad como resuelto.
    """
    try:
        # Buscar el incidente
        incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incidente con ID {incident_id} no encontrado")
        
        # Actualizar incidente
        incident.is_resolved = True
        incident.resolution_notes = notes
        incident.resolved_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "incident_id": incident.id,
            "message": "Incidente marcado como resuelto"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resolviendo incidente: {str(e)}")

@router.get("/sales/report", response_model=Dict[str, Any])
async def get_sales_report(
    period: str = Query("daily", description="Período de agrupación: daily, weekly, monthly"),
    start_date: Optional[str] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Genera un reporte de ventas agrupado por período.
    """
    try:
        # Configurar fechas predeterminadas si no se proporcionan
        if not end_date:
            end_date_obj = datetime.now()
        else:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                end_date_obj = datetime.combine(end_date_obj, datetime.max.time())  # Fin del día
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_fin inválido. Use YYYY-MM-DD")
        
        if not start_date:
            # Por defecto, un mes atrás
            start_date_obj = end_date_obj - timedelta(days=30)
        else:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD")
        
        # Validar el período
        if period not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=400, 
                detail="Período no válido. Use uno de: daily, weekly, monthly"
            )
        
        # Preparar la consulta base
        query = db.query(
            Order.created_at,
            Order.total_amount,
            Order.payment_method
        ).filter(
            Order.status == OrderStatus.COMPLETED.value,
            Order.created_at.between(start_date_obj, end_date_obj)
        ).all()
        
        # Procesar resultados según el período
        result_data = {}
        total_sales = 0
        order_count = 0
        
        for order in query:
            order_date = order.created_at
            amount = order.total_amount
            payment_method = order.payment_method
            
            # Determinar la clave según el período
            if period == "daily":
                key = order_date.strftime("%Y-%m-%d")
            elif period == "weekly":
                # Semana ISO (año-WXX)
                key = f"{order_date.isocalendar()[0]}-W{order_date.isocalendar()[1]:02d}"
            else:  # monthly
                key = order_date.strftime("%Y-%m")
            
            # Inicializar si la clave no existe
            if key not in result_data:
                result_data[key] = {
                    "total": 0,
                    "count": 0,
                    "payment_methods": {}
                }
            
            # Actualizar datos
            result_data[key]["total"] += amount
            result_data[key]["count"] += 1
            
            # Actualizar método de pago
            if payment_method not in result_data[key]["payment_methods"]:
                result_data[key]["payment_methods"][payment_method] = {
                    "total": 0,
                    "count": 0
                }
            
            result_data[key]["payment_methods"][payment_method]["total"] += amount
            result_data[key]["payment_methods"][payment_method]["count"] += 1
            
            # Actualizar totales generales
            total_sales += amount
            order_count += 1
        
        # Ordenar por clave (fecha)
        sorted_data = []
        for key in sorted(result_data.keys()):
            entry = {
                "period": key,
                "total_sales": result_data[key]["total"],
                "order_count": result_data[key]["count"],
                "payment_methods": result_data[key]["payment_methods"]
            }
            sorted_data.append(entry)
        
        return {
            "start_date": start_date_obj.strftime("%Y-%m-%d"),
            "end_date": end_date_obj.strftime("%Y-%m-%d"),
            "period_type": period,
            "total_sales": total_sales,
            "total_orders": order_count,
            "data": sorted_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")