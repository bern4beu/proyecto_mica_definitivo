CREATE TABLE producto_base (
id SERIAL PRIMARY KEY,
codigo_base INT NOT NULL,
nombre VARCHAR(50),
descripcion VARCHAR(50),
imagen_principal BYTEA,
alto NUMERIC(10,2) CHECK (alto > 0),
ancho NUMERIC(10,2) CHECK (ancho > 0),
largo NUMERIC(10,2) CHECK (largo > 0),
diametro NUMERIC(10,2) CHECK (diametro > 0)
);

ALTER TABLE producto_base DROP COLUMN codigo_base;

CREATE TABLE proveedor (
id SERIAL PRIMARY KEY,
nombre VARCHAR(45) NOT NULL
);

CREATE TABLE producto_variante (
id SERIAL PRIMARY KEY,
id_producto_base INT NOT NULL REFERENCES producto_base(id),
marca CITEXT NOT NULL,
calidad VARCHAR(45),
subcodigo INT NOT NULL,
precio NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
precio_compra NUMERIC(10,2) CHECK (precio_compra >= 0),
stock INT NOT NULL CHECK (stock >= 0),
ubicacion VARCHAR(45), 
id_proveedor INT REFERENCES proveedor(id),
CONSTRAINT unique_producto_variante_logica
UNIQUE (id_producto_base, marca)
);

CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE vehiculo (
id SERIAL PRIMARY KEY,
marca CITEXT NOT NULL,
modelo CITEXT NOT NULL,
motor CITEXT,
UNIQUE (marca, modelo, motor)
);

CREATE TABLE producto_vehiculo (
id SERIAL PRIMARY KEY,
id_producto_base INT NOT NULL REFERENCES producto_base(id) ON DELETE CASCADE,
id_vehiculo INT NOT NULL REFERENCES vehiculo(id) ON DELETE CASCADE,
UNIQUE (id_producto_base, id_vehiculo)
);

CREATE TABLE cliente (
id SERIAL PRIMARY KEY,
nombre VARCHAR(45) NOT NULL
);

CREATE TABLE venta (
id SERIAL PRIMARY KEY,
fecha TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
total NUMERIC(10,2),
id_cliente INT REFERENCES cliente(id)
);

ALTER TABLE venta
ADD CONSTRAINT unique_venta UNIQUE(fecha, id_cliente, total);

CREATE TABLE venta_detalle (
id SERIAL PRIMARY KEY,
id_venta INT NOT NULL REFERENCES venta(id) ON DELETE CASCADE,
id_producto_variante INT NOT NULL REFERENCES producto_variante(id),
cantidad INT NOT NULL CHECK (cantidad > 0),
precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0)
);

