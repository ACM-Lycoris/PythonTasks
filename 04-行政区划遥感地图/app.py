"""
中国行政区划 + 遥感数据地图 - Flask 主程序
China Administrative Divisions + Remote Sensing Data Map - Main Flask Application
"""

import sqlite3
from flask import Flask, render_template, jsonify, request, g

app = Flask(__name__)
DATABASE = 'remote_sensing.db'


def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ============================================================
# 主页
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')


# ============================================================
# === 省份相关 API ===
# ============================================================

@app.route('/api/provinces')
def get_provinces():
    """返回所有省份元数据（含简称、省会、人口、面积等）"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.capital, p.abbreviation, p.population, p.area,
               p.intro, p.culture,
               (SELECT COUNT(*) FROM cities c WHERE c.province = p.name) as city_count,
               (SELECT COUNT(*) FROM research_points r WHERE r.province = p.name) as research_count
        FROM provinces p
        ORDER BY p.id
    ''')
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'],
            'name': row['name'],
            'capital': row['capital'],
            'abbreviation': row['abbreviation'],
            'population': row['population'],
            'area': row['area'],
            'intro': row['intro'],
            'culture': row['culture'],
            'city_count': row['city_count'],
            'research_count': row['research_count']
        })

    return jsonify(result)


@app.route('/api/province/<name>')
def get_province_detail(name):
    """返回单个省份详情 + 下属城市列表"""
    db = get_db()
    cursor = db.cursor()

    # 省份基本信息
    cursor.execute('''
        SELECT name, capital, abbreviation, population, area, intro, culture
        FROM provinces WHERE name = ?
    ''', (name,))
    p_row = cursor.fetchone()
    if not p_row:
        return jsonify({'error': '省份未找到'}), 404

    # 下属城市
    cursor.execute('''
        SELECT id, name, longitude, latitude, level, population, gdp
        FROM cities WHERE province = ? ORDER BY id
    ''', (name,))
    cities = []
    for row in cursor.fetchall():
        cities.append({
            'id': row['id'],
            'name': row['name'],
            'longitude': row['longitude'],
            'latitude': row['latitude'],
            'level': row['level'],
            'population': row['population'],
            'gdp': row['gdp']
        })

    return jsonify({
        'name': p_row['name'],
        'capital': p_row['capital'],
        'abbreviation': p_row['abbreviation'],
        'population': p_row['population'],
        'area': p_row['area'],
        'intro': p_row['intro'],
        'culture': p_row['culture'],
        'city_count': len(cities),
        'cities': cities
    })


# ============================================================
# === 城市相关 API ===
# ============================================================

@app.route('/api/cities')
def get_cities():
    """返回所有城市，或按 ?province=xx 筛选"""
    province = request.args.get('province', None)
    db = get_db()
    cursor = db.cursor()

    if province:
        cursor.execute('''
            SELECT id, name, province, longitude, latitude, level, population, gdp
            FROM cities WHERE province = ? ORDER BY id
        ''', (province,))
    else:
        cursor.execute('''
            SELECT id, name, province, longitude, latitude, level, population, gdp
            FROM cities ORDER BY id
        ''')

    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'id': row['id'],
            'name': row['name'],
            'province': row['province'],
            'longitude': row['longitude'],
            'latitude': row['latitude'],
            'level': row['level'],
            'population': row['population'],
            'gdp': row['gdp']
        })
    return jsonify(result)


@app.route('/api/city/<int:city_id>')
def get_city_detail(city_id):
    """返回单个城市的完整信息"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM cities WHERE id = ?', (city_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': '城市未找到'}), 404

    return jsonify({
        'id': row['id'],
        'name': row['name'],
        'province': row['province'],
        'longitude': row['longitude'],
        'latitude': row['latitude'],
        'level': row['level'],
        'intro': row['intro'],
        'culture': row['culture'],
        'population': row['population'],
        'area': row['area'],
        'gdp': row['gdp'],
        'climate': row['climate'],
        'attractions': row['attractions'],
        'established': row['established']
    })


@app.route('/api/search')
def search_cities():
    """城市/省份模糊搜索, ?q=xxx —— 同时返回省份和城市匹配结果"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    db = get_db()
    cursor = db.cursor()
    pattern = f'%{q}%'

    result = []

    # 1. 搜索匹配的省份
    cursor.execute('''
        SELECT id, name, capital, abbreviation, population, area, intro, culture
        FROM provinces
        WHERE name LIKE ? OR capital LIKE ? OR abbreviation LIKE ?
        LIMIT 8
    ''', (pattern, pattern, pattern))
    for row in cursor.fetchall():
        # 获取该省城市数量
        cursor.execute('SELECT COUNT(*) FROM cities WHERE province = ?', (row['name'],))
        city_count = cursor.fetchone()[0]
        # 获取省会经纬度
        cursor.execute('SELECT longitude, latitude FROM cities WHERE name = ? AND province = ? LIMIT 1',
                       (row['capital'], row['name']))
        cap_row = cursor.fetchone()
        result.append({
            'type': 'province',
            'id': row['id'],
            'name': row['name'],
            'capital': row['capital'],
            'abbreviation': row['abbreviation'],
            'population': row['population'],
            'area': row['area'],
            'city_count': city_count,
            'longitude': cap_row['longitude'] if cap_row else None,
            'latitude': cap_row['latitude'] if cap_row else None
        })

    # 2. 搜索匹配的城市
    cursor.execute('''
        SELECT id, name, province, longitude, latitude, level, population
        FROM cities
        WHERE name LIKE ? OR province LIKE ?
        LIMIT 30
    ''', (pattern, pattern))

    for row in cursor.fetchall():
        result.append({
            'type': 'city',
            'id': row['id'],
            'name': row['name'],
            'province': row['province'],
            'longitude': row['longitude'],
            'latitude': row['latitude'],
            'level': row['level'],
            'population': row['population']
        })

    # 3. 搜索匹配的区县
    cursor.execute('''
        SELECT d.id, d.name, d.city_id, d.city_name, d.province_name,
               d.longitude, d.latitude, d.type, d.population
        FROM districts d
        WHERE d.name LIKE ?
        LIMIT 20
    ''', (pattern,))

    for row in cursor.fetchall():
        result.append({
            'type': 'district',
            'id': row['id'],
            'name': row['name'],
            'city_id': row['city_id'],
            'city_name': row['city_name'],
            'province': row['province_name'],
            'longitude': row['longitude'],
            'latitude': row['latitude'],
            'district_type': row['type'],
            'population': row['population']
        })

    return jsonify(result)


# ============================================================
# === 区县相关 API ===
# ============================================================

@app.route('/api/districts')
def get_districts():
    """返回区县数据，支持 ?city_id=xx / ?province=xx / 范围筛选"""
    city_id = request.args.get('city_id', type=int)
    province = request.args.get('province', None)
    min_lat = request.args.get('min_lat', type=float)
    max_lat = request.args.get('max_lat', type=float)
    min_lng = request.args.get('min_lng', type=float)
    max_lng = request.args.get('max_lng', type=float)

    db = get_db()
    cursor = db.cursor()

    query = '''SELECT id, name, city_id, city_name, province_name,
                      longitude, latitude, type, population, area
               FROM districts'''
    conditions = []
    params = []

    if city_id:
        conditions.append('city_id = ?')
        params.append(city_id)
    if province:
        conditions.append('province_name = ?')
        params.append(province)
    if all([min_lat is not None, max_lat is not None, min_lng is not None, max_lng is not None]):
        conditions.append('latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?')
        params.extend([min_lat, max_lat, min_lng, max_lng])

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY city_id, id'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'],
            'name': row['name'],
            'city_id': row['city_id'],
            'city_name': row['city_name'],
            'province_name': row['province_name'],
            'longitude': row['longitude'],
            'latitude': row['latitude'],
            'type': row['type'],
            'population': row['population'],
            'area': row['area']
        })
    return jsonify(result)


@app.route('/api/district/<int:district_id>')
def get_district_detail(district_id):
    """返回单个区县的完整信息"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM districts WHERE id = ?', (district_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': '区县未找到'}), 404

    return jsonify({
        'id': row['id'],
        'name': row['name'],
        'city_id': row['city_id'],
        'city_name': row['city_name'],
        'province_name': row['province_name'],
        'longitude': row['longitude'],
        'latitude': row['latitude'],
        'type': row['type'],
        'population': row['population'],
        'area': row['area']
    })


# ============================================================
# === 遥感研究数据点 API (兼容原有) ===
# ============================================================

@app.route('/api/points')
def get_points():
    """返回所有遥感研究数据点 (支持 ?province=xx 和 ?year=xxx 筛选)"""
    province = request.args.get('province', None)
    year = request.args.get('year', None)

    db = get_db()
    cursor = db.cursor()

    query = 'SELECT * FROM research_points'
    conditions, params = [], []

    if province:
        conditions.append('province = ?')
        params.append(province)
    if year:
        conditions.append('year = ?')
        params.append(int(year))

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY id'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    points = []
    for row in rows:
        points.append({
            'id': row['id'],
            'longitude': row['longitude'],
            'latitude': row['latitude'],
            'author': row['author'],
            'institution': row['institution'],
            'overview': row['overview'],
            'title': row['title'],
            'province': row['province'],
            'year': row['year']
        })
    return jsonify(points)


@app.route('/api/years')
def get_years():
    """返回所有研究年份列表"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT year FROM research_points WHERE year IS NOT NULL ORDER BY year')
    return jsonify([row[0] for row in cursor.fetchall()])


# ============================================================
# === 全局统计 API ===
# ============================================================

@app.route('/api/stats')
def get_stats():
    """全局统计信息"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT COUNT(*) FROM provinces')
    province_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM cities')
    city_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM districts')
    district_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM research_points')
    research_count = cursor.fetchone()[0]

    cursor.execute('SELECT MIN(year), MAX(year) FROM research_points WHERE year IS NOT NULL')
    year_range = cursor.fetchone()

    cursor.execute('SELECT SUM(population) FROM cities')
    total_pop = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(gdp) FROM cities')
    total_gdp = cursor.fetchone()[0] or 0

    return jsonify({
        'province_count': province_count,
        'city_count': city_count,
        'district_count': district_count,
        'research_count': research_count,
        'total_points': research_count,  # 兼容旧字段
        'year_min': year_range[0],
        'year_max': year_range[1],
        'total_population_wan': round(total_pop, 1),
        'total_gdp_yi': round(total_gdp, 1)
    })


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
