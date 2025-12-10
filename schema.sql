-- HandyMan Platform Database Schema
-- PostgreSQL with PostGIS Extension

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users Table (Homeowners)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);

-- Locations Table (User Properties)
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    country VARCHAR(50) DEFAULT 'USA',
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,  -- PostGIS point
    is_primary BOOLEAN DEFAULT FALSE,
    nickname VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_locations_user ON locations(user_id);
CREATE INDEX idx_locations_coordinates ON locations USING GIST(coordinates);

-- Providers Table (Gig Workers)
CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    current_location GEOGRAPHY(POINT, 4326),  -- Real-time location
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'suspended', 'rejected')),
    is_active BOOLEAN DEFAULT TRUE,
    is_available BOOLEAN DEFAULT TRUE,
    job_types JSONB NOT NULL,  -- ["snow_removal", "lawn_care", "handyman"]
    hourly_rate DECIMAL(10, 2),
    average_rating DECIMAL(3, 2) DEFAULT 0.0,
    total_jobs INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_providers_email ON providers(email);
CREATE INDEX idx_providers_status ON providers(status);
CREATE INDEX idx_providers_location ON providers USING GIST(current_location);
CREATE INDEX idx_providers_job_types ON providers USING GIN(job_types);

-- Provider Verifications Table
CREATE TABLE provider_verifications (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,  -- 'id', 'license', 'insurance', 'certification'
    document_url VARCHAR(500) NOT NULL,
    extracted_data JSONB,  -- OCR results
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by INTEGER,  -- Admin user ID
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_verifications_provider ON provider_verifications(provider_id);

-- Jobs Table (Polymorphic for all service types)
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN ('snow_removal', 'lawn_care', 'handyman', 'plumbing', 'electrical', 'carpentry', 'other')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    estimated_square_footage DECIMAL(10, 2),  -- From AI/CV
    severity VARCHAR(20) CHECK (severity IN ('light', 'moderate', 'heavy', 'severe')),
    ai_confidence DECIMAL(5, 4),  -- 0.0 to 1.0
    estimated_price DECIMAL(10, 2) NOT NULL,
    surge_multiplier DECIMAL(5, 2) DEFAULT 1.0,
    final_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_progress', 'completed', 'cancelled', 'expired')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    extra_data JSONB,  -- Flexible for different job types
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_location ON jobs(location_id);
CREATE INDEX idx_jobs_type ON jobs(job_type);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created ON jobs(created_at);

-- Job Images Table
CREATE TABLE job_images (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    image_type VARCHAR(50),
    analysis_results JSONB,  -- CV model output
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_job_images_job ON job_images(job_id);

-- Job Assignments Table
CREATE TABLE job_assignments (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE UNIQUE,
    provider_id INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    accepted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review TEXT
);

CREATE INDEX idx_assignments_job ON job_assignments(job_id);
CREATE INDEX idx_assignments_provider ON job_assignments(provider_id);

-- Geospatial Query Examples

-- Find all pending jobs within 10km of a provider's location
-- EXAMPLE: 
-- SELECT j.*, 
--        ST_Distance(l.coordinates, ST_SetSRID(ST_MakePoint(-122.4194, 37.7749), 4326)::geography) / 1000 as distance_km
-- FROM jobs j
-- JOIN locations l ON j.location_id = l.id
-- WHERE j.status = 'pending' 
--   AND ST_DWithin(l.coordinates, ST_SetSRID(ST_MakePoint(-122.4194, 37.7749), 4326)::geography, 10000)
-- ORDER BY distance_km;

-- Find available providers within radius of a job
-- EXAMPLE:
-- SELECT p.*, 
--        ST_Distance(p.current_location, ST_SetSRID(ST_MakePoint(-122.4194, 37.7749), 4326)::geography) / 1000 as distance_km
-- FROM providers p
-- WHERE p.is_available = TRUE 
--   AND p.status = 'verified'
--   AND ST_DWithin(p.current_location, ST_SetSRID(ST_MakePoint(-122.4194, 37.7749), 4326)::geography, 10000)
-- ORDER BY distance_km;
