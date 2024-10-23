-- Script para crear tablas en la base de datos landing_zone
-- Asegúrate de estar conectado a la base de datos landing_zone antes de ejecutar este script.

-- Tabla que almacena información básica de las empresas
CREATE TABLE IF NOT EXISTS basic_info (
    symbol VARCHAR(10) PRIMARY KEY, -- Símbolo único de la empresa
    industry VARCHAR(100),           -- Industria a la que pertenece la empresa
    sector VARCHAR(100),             -- Sector de la economía
    employee_count INTEGER,          -- Número de empleados
    city VARCHAR(100),               -- Ciudad donde se encuentra la empresa
    phone VARCHAR(15),               -- Número de teléfono de contacto
    state VARCHAR(50),               -- Estado donde se ubica la empresa
    country VARCHAR(50),             -- País donde se encuentra
    website VARCHAR(255),            -- URL del sitio web de la empresa
    address VARCHAR(255)             -- Dirección física de la empresa
);

-- Tabla que almacena datos de precios históricos de las acciones
CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,           -- Identificador único para cada entrada
    symbol VARCHAR(10),              -- Símbolo de la empresa (clave foránea)
    date DATE,                       -- Fecha del registro
    open FLOAT,                      -- Precio de apertura
    high FLOAT,                      -- Precio más alto del día
    low FLOAT,                       -- Precio más bajo del día
    close FLOAT,                     -- Precio de cierre
    volume BIGINT,                  -- Volumen de acciones transaccionadas
    FOREIGN KEY (symbol) REFERENCES basic_info(symbol) ON DELETE CASCADE, -- Relación con basic_info
    UNIQUE (symbol, date)           -- Asegura que no haya entradas duplicadas para el mismo símbolo en la misma fecha
);

-- Tabla que almacena información financiera fundamental de las empresas
CREATE TABLE IF NOT EXISTS fundamentals (
    id SERIAL PRIMARY KEY,           -- Identificador único para cada entrada
    symbol VARCHAR(10),              -- Símbolo de la empresa (clave foránea)
    assets FLOAT,                    -- Activos totales
    debt FLOAT,                      -- Deuda total
    invested_capital FLOAT,          -- Capital invertido
    shares_issued FLOAT,             -- Acciones emitidas
    FOREIGN KEY (symbol) REFERENCES basic_info(symbol) ON DELETE CASCADE, -- Relación con basic_info
    UNIQUE (symbol)                  -- Asegura que cada símbolo tenga solo un registro de fundamentos
);

-- Tabla que almacena información sobre los titulares de acciones
CREATE TABLE IF NOT EXISTS holders (
    id SERIAL PRIMARY KEY,           -- Identificador único para cada entrada
    date DATE,                       -- Fecha del registro
    holder VARCHAR(255),             -- Nombre del titular
    shares BIGINT,                   -- Número de acciones que posee
    value FLOAT,                     -- Valor de las acciones que posee
    symbol VARCHAR(10),              -- Símbolo de la empresa (clave foránea)
    FOREIGN KEY (symbol) REFERENCES basic_info(symbol) ON DELETE CASCADE, -- Relación con basic_info
    UNIQUE (date, holder, symbol)    -- Asegura que la combinación de fecha, titular y símbolo sea única
);

-- Tabla que almacena actualizaciones y rebajas de calificación de acciones
CREATE TABLE IF NOT EXISTS upgrades_downgrades (
    id SERIAL PRIMARY KEY,           -- Identificador único para cada entrada
    date DATE,                       -- Fecha de la calificación
    firm VARCHAR(255),               -- Firma que emite la calificación
    to_grade VARCHAR(255),           -- Nueva calificación
    from_grade VARCHAR(255),         -- Calificación anterior
    action VARCHAR(50),              -- Acción (upgrade o downgrade)
    symbol VARCHAR(10),              -- Símbolo de la empresa (clave foránea)
    FOREIGN KEY (symbol) REFERENCES basic_info(symbol) ON DELETE CASCADE, -- Relación con basic_info
    UNIQUE (date, firm, symbol)      -- Asegura que la combinación de fecha, firma y símbolo sea única
);