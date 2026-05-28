"""
Airport coordinate lookup table for Haversine distance calculation.

Top 50 global airports by passenger traffic with IATA codes,
coordinates (lat/lon), city, and country.
"""
import math

AIRPORTS = {
    'ATL': {'name': 'Hartsfield-Jackson Atlanta', 'lat': 33.6407, 'lon': -84.4277, 'city': 'Atlanta', 'country': 'US'},
    'DFW': {'name': 'Dallas/Fort Worth', 'lat': 32.8998, 'lon': -97.0403, 'city': 'Dallas', 'country': 'US'},
    'DEN': {'name': 'Denver International', 'lat': 39.8561, 'lon': -104.6737, 'city': 'Denver', 'country': 'US'},
    'ORD': {'name': "Chicago O'Hare", 'lat': 41.9742, 'lon': -87.9073, 'city': 'Chicago', 'country': 'US'},
    'LAX': {'name': 'Los Angeles International', 'lat': 33.9425, 'lon': -118.4081, 'city': 'Los Angeles', 'country': 'US'},
    'JFK': {'name': 'John F. Kennedy International', 'lat': 40.6413, 'lon': -73.7781, 'city': 'New York', 'country': 'US'},
    'SFO': {'name': 'San Francisco International', 'lat': 37.6213, 'lon': -122.3790, 'city': 'San Francisco', 'country': 'US'},
    'SEA': {'name': 'Seattle-Tacoma', 'lat': 47.4502, 'lon': -122.3088, 'city': 'Seattle', 'country': 'US'},
    'MIA': {'name': 'Miami International', 'lat': 25.7959, 'lon': -80.2870, 'city': 'Miami', 'country': 'US'},
    'EWR': {'name': 'Newark Liberty', 'lat': 40.6895, 'lon': -74.1745, 'city': 'Newark', 'country': 'US'},
    'BOS': {'name': 'Boston Logan', 'lat': 42.3656, 'lon': -71.0096, 'city': 'Boston', 'country': 'US'},
    'IAH': {'name': 'George Bush Houston', 'lat': 29.9902, 'lon': -95.3368, 'city': 'Houston', 'country': 'US'},
    'MSP': {'name': 'Minneapolis-Saint Paul', 'lat': 44.8848, 'lon': -93.2223, 'city': 'Minneapolis', 'country': 'US'},
    'PHX': {'name': 'Phoenix Sky Harbor', 'lat': 33.4373, 'lon': -112.0078, 'city': 'Phoenix', 'country': 'US'},
    'LAS': {'name': 'Harry Reid Las Vegas', 'lat': 36.0840, 'lon': -115.1537, 'city': 'Las Vegas', 'country': 'US'},
    'YYZ': {'name': 'Toronto Pearson', 'lat': 43.6777, 'lon': -79.6248, 'city': 'Toronto', 'country': 'CA'},
    'YVR': {'name': 'Vancouver International', 'lat': 49.1947, 'lon': -123.1792, 'city': 'Vancouver', 'country': 'CA'},
    'MEX': {'name': 'Mexico City International', 'lat': 19.4363, 'lon': -99.0721, 'city': 'Mexico City', 'country': 'MX'},
    'GRU': {'name': 'São Paulo-Guarulhos', 'lat': -23.4356, 'lon': -46.4731, 'city': 'São Paulo', 'country': 'BR'},
    'EZE': {'name': 'Buenos Aires Ezeiza', 'lat': -34.8222, 'lon': -58.5358, 'city': 'Buenos Aires', 'country': 'AR'},
    'BOG': {'name': 'El Dorado Bogotá', 'lat': 4.7016, 'lon': -74.1469, 'city': 'Bogotá', 'country': 'CO'},
    'SCL': {'name': 'Santiago International', 'lat': -33.3930, 'lon': -70.7858, 'city': 'Santiago', 'country': 'CL'},
    'LHR': {'name': 'London Heathrow', 'lat': 51.4700, 'lon': -0.4543, 'city': 'London', 'country': 'GB'},
    'CDG': {'name': 'Paris Charles de Gaulle', 'lat': 49.0097, 'lon': 2.5479, 'city': 'Paris', 'country': 'FR'},
    'FRA': {'name': 'Frankfurt Airport', 'lat': 50.0379, 'lon': 8.5622, 'city': 'Frankfurt', 'country': 'DE'},
    'AMS': {'name': 'Amsterdam Schiphol', 'lat': 52.3105, 'lon': 4.7683, 'city': 'Amsterdam', 'country': 'NL'},
    'MAD': {'name': 'Madrid Barajas', 'lat': 40.4983, 'lon': -3.5676, 'city': 'Madrid', 'country': 'ES'},
    'BCN': {'name': 'Barcelona El Prat', 'lat': 41.2971, 'lon': 2.0785, 'city': 'Barcelona', 'country': 'ES'},
    'FCO': {'name': 'Rome Fiumicino', 'lat': 41.8003, 'lon': 12.2389, 'city': 'Rome', 'country': 'IT'},
    'MUC': {'name': 'Munich Airport', 'lat': 48.3537, 'lon': 11.7750, 'city': 'Munich', 'country': 'DE'},
    'ZRH': {'name': 'Zurich Airport', 'lat': 47.4647, 'lon': 8.5492, 'city': 'Zurich', 'country': 'CH'},
    'VIE': {'name': 'Vienna International', 'lat': 48.1103, 'lon': 16.5697, 'city': 'Vienna', 'country': 'AT'},
    'IST': {'name': 'Istanbul Airport', 'lat': 41.2753, 'lon': 28.7519, 'city': 'Istanbul', 'country': 'TR'},
    'DXB': {'name': 'Dubai International', 'lat': 25.2532, 'lon': 55.3657, 'city': 'Dubai', 'country': 'AE'},
    'DOH': {'name': 'Hamad International', 'lat': 25.2731, 'lon': 51.6081, 'city': 'Doha', 'country': 'QA'},
    'SIN': {'name': 'Singapore Changi', 'lat': 1.3644, 'lon': 103.9915, 'city': 'Singapore', 'country': 'SG'},
    'HKG': {'name': 'Hong Kong International', 'lat': 22.3080, 'lon': 113.9185, 'city': 'Hong Kong', 'country': 'HK'},
    'NRT': {'name': 'Tokyo Narita', 'lat': 35.7720, 'lon': 140.3929, 'city': 'Tokyo', 'country': 'JP'},
    'HND': {'name': 'Tokyo Haneda', 'lat': 35.5494, 'lon': 139.7798, 'city': 'Tokyo', 'country': 'JP'},
    'ICN': {'name': 'Seoul Incheon', 'lat': 37.4602, 'lon': 126.4407, 'city': 'Seoul', 'country': 'KR'},
    'PEK': {'name': 'Beijing Capital', 'lat': 40.0799, 'lon': 116.6031, 'city': 'Beijing', 'country': 'CN'},
    'PVG': {'name': 'Shanghai Pudong', 'lat': 31.1443, 'lon': 121.8083, 'city': 'Shanghai', 'country': 'CN'},
    'BOM': {'name': 'Mumbai Chhatrapati Shivaji', 'lat': 19.0896, 'lon': 72.8656, 'city': 'Mumbai', 'country': 'IN'},
    'DEL': {'name': 'Delhi Indira Gandhi', 'lat': 28.5562, 'lon': 77.1000, 'city': 'Delhi', 'country': 'IN'},
    'BLR': {'name': 'Bangalore Kempegowda', 'lat': 13.1986, 'lon': 77.7066, 'city': 'Bangalore', 'country': 'IN'},
    'SYD': {'name': 'Sydney Kingsford Smith', 'lat': -33.9461, 'lon': 151.1772, 'city': 'Sydney', 'country': 'AU'},
    'MEL': {'name': 'Melbourne Tullamarine', 'lat': -37.6690, 'lon': 144.8410, 'city': 'Melbourne', 'country': 'AU'},
    'JNB': {'name': 'Johannesburg O.R. Tambo', 'lat': -26.1392, 'lon': 28.2460, 'city': 'Johannesburg', 'country': 'ZA'},
    'CAI': {'name': 'Cairo International', 'lat': 30.1219, 'lon': 31.4056, 'city': 'Cairo', 'country': 'EG'},
    'NBO': {'name': 'Nairobi Jomo Kenyatta', 'lat': -1.3192, 'lon': 36.9278, 'city': 'Nairobi', 'country': 'KE'},
    'LOS': {'name': 'Lagos Murtala Muhammed', 'lat': 6.5774, 'lon': 3.3212, 'city': 'Lagos', 'country': 'NG'},
    'CPT': {'name': 'Cape Town International', 'lat': -33.9649, 'lon': 18.6017, 'city': 'Cape Town', 'country': 'ZA'},
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points on Earth.
    
    Uses the Haversine formula. Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_airport(code: str) -> dict | None:
    """Look up airport by IATA code (case-insensitive)."""
    return AIRPORTS.get(code.upper().strip()) if code else None


def calculate_flight_distance(origin: str, destination: str) -> float | None:
    """
    Calculate distance between two airports by IATA code.
    Returns distance in km or None if either airport is not found.
    """
    orig = get_airport(origin)
    dest = get_airport(destination)
    if not orig or not dest:
        return None
    return haversine_distance(orig['lat'], orig['lon'], dest['lat'], dest['lon'])
