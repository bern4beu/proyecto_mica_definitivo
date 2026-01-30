ALTER TABLE producto_variante
DROP CONSTRAINT unique_producto_variante;

ALTER TABLE producto_variante
ADD CONSTRAINT unique_producto_variante_logica
UNIQUE (id_producto_base, marca);
