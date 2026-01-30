CREATE OR REPLACE FUNCTION descontar_stock()
RETURNS TRIGGER AS $$
DECLARE
    stock_disponible INT;
BEGIN
    -- Obtener stock actual del producto variante
    SELECT stock
    INTO stock_disponible
    FROM producto_variante
    WHERE id = NEW.id_producto_variante
    FOR UPDATE;

    -- Validar stock suficiente
    IF stock_disponible < NEW.cantidad THEN
        RAISE EXCEPTION
            'Stock insuficiente para el producto variante % (disponible: %, solicitado: %)',
            NEW.id_producto_variante, stock_disponible, NEW.cantidad;
    END IF;

    -- Descontar stock
    UPDATE producto_variante
    SET stock = stock - NEW.cantidad
    WHERE id = NEW.id_producto_variante;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_descontar_stock
AFTER INSERT ON venta_detalle
FOR EACH ROW
EXECUTE FUNCTION descontar_stock();

CREATE OR REPLACE FUNCTION generar_subcodigo()
RETURNS TRIGGER AS $$
DECLARE
    max_sub INT;
BEGIN
    SELECT COALESCE(MAX(subcodigo), 0)
    INTO max_sub
    FROM producto_variante
    WHERE id_producto_base = NEW.id_producto_base;

    NEW.subcodigo := max_sub + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generar_subcodigo
BEFORE INSERT ON producto_variante
FOR EACH ROW
WHEN (NEW.subcodigo IS NULL)
EXECUTE FUNCTION generar_subcodigo();


