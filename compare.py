# Comparison module for comparing predictions across time periods

from flask import Blueprint, render_template, request, jsonify
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

compare_bp = Blueprint('compare', __name__, url_prefix='/compare')


def register_compare_routes(app, db):
    """Register comparison routes"""
    
    @compare_bp.route('/')
    def compare_page():
        """Comparison tool page"""
        areas = db.execute_query('SELECT DISTINCT area FROM prediction_logs', fetch_all=True)
        waste_types = db.execute_query('SELECT DISTINCT waste_type FROM prediction_logs', fetch_all=True)
        
        return render_template(
            'compare.html',
            areas=[a[0] for a in areas] if areas else [],
            waste_types=[t[0] for t in waste_types] if waste_types else []
        )
    
    @compare_bp.route('/api/data')
    def get_comparison_data():
        """Get comparison data for two time periods"""
        area = request.args.get('area', '')
        waste_type = request.args.get('waste_type', '')
        period1_start = request.args.get('period1_start', '')
        period1_end = request.args.get('period1_end', '')
        period2_start = request.args.get('period2_start', '')
        period2_end = request.args.get('period2_end', '')
        
        result = {
            'period1': {'predictions': [], 'summary': {}},
            'period2': {'predictions': [], 'summary': {}},
            'comparison': {}
        }
        
        try:
            # Build base query
            base_conditions = []
            params1 = []
            params2 = []
            
            if area:
                base_conditions.append('area = ?')
                params1.append(area)
                params2.append(area)
            
            if waste_type:
                base_conditions.append('waste_type = ?')
                params1.append(waste_type)
                params2.append(waste_type)
            
            where_clause = ' AND '.join(base_conditions) if base_conditions else '1=1'
            
            # Period 1 data
            if period1_start and period1_end:
                query1 = f'''
                    SELECT prediction_date, predicted_weight_kg, area, waste_type
                    FROM prediction_logs 
                    WHERE {where_clause} 
                    AND prediction_date BETWEEN ? AND ?
                    ORDER BY prediction_date
                '''
                p1_data = db.execute_query(
                    query1, 
                    (*params1, period1_start, period1_end), 
                    fetch_all=True
                )
                
                if p1_data:
                    result['period1']['predictions'] = [
                        {'date': r[0], 'weight': r[1], 'area': r[2], 'type': r[3]} 
                        for r in p1_data
                    ]
                    
                    # Summary for period 1
                    summary1 = db.execute_query(f'''
                        SELECT COUNT(*), AVG(predicted_weight_kg), 
                               SUM(predicted_weight_kg), MIN(predicted_weight_kg), 
                               MAX(predicted_weight_kg)
                        FROM prediction_logs 
                        WHERE {where_clause} 
                        AND prediction_date BETWEEN ? AND ?
                    ''', (*params1, period1_start, period1_end), fetch_one=True)
                    
                    if summary1:
                        result['period1']['summary'] = {
                            'count': summary1[0],
                            'avg': round(summary1[1] or 0, 2),
                            'total': round(summary1[2] or 0, 2),
                            'min': round(summary1[3] or 0, 2),
                            'max': round(summary1[4] or 0, 2)
                        }
            
            # Period 2 data
            if period2_start and period2_end:
                query2 = f'''
                    SELECT prediction_date, predicted_weight_kg, area, waste_type
                    FROM prediction_logs 
                    WHERE {where_clause} 
                    AND prediction_date BETWEEN ? AND ?
                    ORDER BY prediction_date
                '''
                p2_data = db.execute_query(
                    query2, 
                    (*params2, period2_start, period2_end), 
                    fetch_all=True
                )
                
                if p2_data:
                    result['period2']['predictions'] = [
                        {'date': r[0], 'weight': r[1], 'area': r[2], 'type': r[3]} 
                        for r in p2_data
                    ]
                    
                    # Summary for period 2
                    summary2 = db.execute_query(f'''
                        SELECT COUNT(*), AVG(predicted_weight_kg), 
                               SUM(predicted_weight_kg), MIN(predicted_weight_kg), 
                               MAX(predicted_weight_kg)
                        FROM prediction_logs 
                        WHERE {where_clause} 
                        AND prediction_date BETWEEN ? AND ?
                    ''', (*params2, period2_start, period2_end), fetch_one=True)
                    
                    if summary2:
                        result['period2']['summary'] = {
                            'count': summary2[0],
                            'avg': round(summary2[1] or 0, 2),
                            'total': round(summary2[2] or 0, 2),
                            'min': round(summary2[3] or 0, 2),
                            'max': round(summary2[4] or 0, 2)
                        }
            
            # Calculate comparison
            if result['period1']['summary'] and result['period2']['summary']:
                p1 = result['period1']['summary']
                p2 = result['period2']['summary']
                
                def calc_change(old, new):
                    if old == 0:
                        return 100 if new > 0 else 0
                    return round(((new - old) / old) * 100, 1)
                
                result['comparison'] = {
                    'count_change': calc_change(p1['count'], p2['count']),
                    'avg_change': calc_change(p1['avg'], p2['avg']),
                    'total_change': calc_change(p1['total'], p2['total']),
                    'avg_diff': round(p2['avg'] - p1['avg'], 2),
                    'total_diff': round(p2['total'] - p1['total'], 2)
                }
            
        except Exception as e:
            logger.error(f"Comparison query failed: {e}")
            return jsonify({'error': str(e)}), 500
        
        return jsonify(result)
    
    @compare_bp.route('/api/quick')
    def quick_comparison():
        """Quick comparison with preset time periods"""
        period = request.args.get('period', 'week')  # week, month, year
        
        today = datetime.now().date()
        
        if period == 'week':
            current_start = today - timedelta(days=7)
            current_end = today
            previous_start = today - timedelta(days=14)
            previous_end = today - timedelta(days=7)
        elif period == 'month':
            current_start = today - timedelta(days=30)
            current_end = today
            previous_start = today - timedelta(days=60)
            previous_end = today - timedelta(days=30)
        else:  # year
            current_start = today - timedelta(days=365)
            current_end = today
            previous_start = today - timedelta(days=730)
            previous_end = today - timedelta(days=365)
        
        result = {
            'current': {},
            'previous': {},
            'change': {}
        }
        
        try:
            # Current period
            current = db.execute_query('''
                SELECT COUNT(*), AVG(predicted_weight_kg), SUM(predicted_weight_kg)
                FROM prediction_logs 
                WHERE prediction_date BETWEEN ? AND ?
            ''', (current_start.isoformat(), current_end.isoformat()), fetch_one=True)
            
            if current:
                result['current'] = {
                    'count': current[0] or 0,
                    'avg': round(current[1] or 0, 2),
                    'total': round(current[2] or 0, 2)
                }
            
            # Previous period
            previous = db.execute_query('''
                SELECT COUNT(*), AVG(predicted_weight_kg), SUM(predicted_weight_kg)
                FROM prediction_logs 
                WHERE prediction_date BETWEEN ? AND ?
            ''', (previous_start.isoformat(), previous_end.isoformat()), fetch_one=True)
            
            if previous:
                result['previous'] = {
                    'count': previous[0] or 0,
                    'avg': round(previous[1] or 0, 2),
                    'total': round(previous[2] or 0, 2)
                }
            
            # Calculate changes
            if result['current'] and result['previous']:
                def calc_change(old, new):
                    if old == 0:
                        return 100 if new > 0 else 0
                    return round(((new - old) / old) * 100, 1)
                
                result['change'] = {
                    'count': calc_change(result['previous']['count'], result['current']['count']),
                    'avg': calc_change(result['previous']['avg'], result['current']['avg']),
                    'total': calc_change(result['previous']['total'], result['current']['total'])
                }
            
        except Exception as e:
            logger.error(f"Quick comparison failed: {e}")
        
        return jsonify(result)
    
    app.register_blueprint(compare_bp)
