# Supabase PostgreSQL Setup for SCHBC BBMS

## 필요한 정보

사용자에게 다음 정보를 요청해야 합니다:

1. **Supabase Database URL** (PostgreSQL connection string)
   - 형식: `postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres`
   - Supabase Dashboard → Settings → Database → Connection String (Session mode)

2. **Supabase Project URL**
   - 형식: `https://[project-ref].supabase.co`
   - Supabase Dashboard → Settings → API → Project URL

3. **Supabase Anon Key** (Public API key)
   - Supabase Dashboard → Settings → API → Project API keys → anon/public

## 생성할 테이블

### 1. users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    emp_id VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. master_config
```sql
CREATE TABLE master_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. blood_master
```sql
CREATE TABLE blood_master (
    id SERIAL PRIMARY KEY,
    component VARCHAR(20) NOT NULL,
    preparation VARCHAR(50) NOT NULL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (component, preparation)
);
```

### 4. safety_config
```sql
CREATE TABLE safety_config (
    id SERIAL PRIMARY KEY,
    blood_type VARCHAR(5) NOT NULL,
    prep_id INTEGER NOT NULL REFERENCES blood_master(id),
    safety_qty INTEGER NOT NULL DEFAULT 0,
    alert_threshold INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (blood_type, prep_id)
);
```

### 5. blood_inventory
```sql
CREATE TABLE blood_inventory (
    id SERIAL PRIMARY KEY,
    blood_type VARCHAR(5) NOT NULL,
    prep_id INTEGER NOT NULL REFERENCES blood_master(id),
    current_qty INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (blood_type, prep_id)
);
```

### 6. stock_log
```sql
CREATE TABLE stock_log (
    id SERIAL PRIMARY KEY,
    blood_type VARCHAR(5) NOT NULL,
    prep_id INTEGER NOT NULL REFERENCES blood_master(id),
    in_qty INTEGER NOT NULL DEFAULT 0,
    out_qty INTEGER NOT NULL DEFAULT 0,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 초기 데이터

### TEST001 사용자
```sql
INSERT INTO users (emp_id, password_hash, name, email)
VALUES ('TEST001', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Ky', '테스트사용자', 'test001@schbc.ac.kr');
```

### RBC 비율 설정
```sql
INSERT INTO master_config (config_key, config_value, description)
VALUES ('rbc_ratio_percent', '50', 'PRBC vs Prefiltered RBC ratio percentage');
```

### blood_master 데이터
```sql
INSERT INTO blood_master (component, preparation, volume) VALUES
('RBC', 'PRBC', 320),
('RBC', 'Prefiltered', 320),
('PLT', 'PC', 200),
('PLT', 'SDP', 200),
('FFP', 'FFP', 250),
('Cryo', 'Cryo', 50);
```
