-- Creamos un usuario nuevo para la web
CREATE USER web_user WITH PASSWORD 'bernabeu912';

-- Le damos permisos sobre la base de datos
GRANT ALL PRIVILEGES ON DATABASE proyecto_mica TO web_user;

-- Dar permisos de todo a web_user en todas las tablas existentes
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO web_user;

-- Dar permisos de usar secuencias (para SERIAL / id autoincrement)
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO web_user;
