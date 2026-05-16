# Analytics module for advanced data analysis

import sqlite3
from flask import Blueprint, render_template, jsonify
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)


def register_analytics_routes(app, db):
    """Register analytics routes"""
    
    @analytics_bp.route('/analytics')
    def analytics_page():
        """Render the analytics dashboard"""
        return render_template('analytics.html')
    
    @analytics_bp.route('/api/analytics/trends')
    def get_trends():
        """Get prediction trends over time"""
        try:
            # Daily trends for last 30 days
            daily = db.execute_query('''
                SELECT prediction_date, 
                       COUNT(*) as count,
                       AVG(predicted_weight_kg) as avg_weight,
                       SUM(predicted_weight_kg) as total_weight
                FROM prediction_logs 
                WHERE prediction_date >= date('now', '-30 days')
                GROUP BY prediction_date 
                ORDER BY prediction_date
            ''', fetch_all=True)
            
            # Weekly trends
            weekly = db.execute_query('''
                SELECT strftime('%Y-W%W', prediction_date) as week,
                       COUNT(*) as count,
                       AVG(predicted_weight_kg) as avg_weight,
                       SUM(predicted_weight_kg) as total_weight
                FROM prediction_logs 
                GROUP BY week
                ORDER BY week DESC
                LIMIT 12
            ''', fetch_all=True)
            
            # Monthly trends
            monthly = db.execute_query('''
                SELECT strftime('%Y-%m', prediction_date) as month,
                       COUNT(*) as count,
                       AVG(predicted_weight_kg) as avg_weight,
                       SUM(predicted_weight_kg) as total_weight
                FROM prediction_logs 
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            ''', fetch_all=True)
            
            return jsonify({
                'daily': [{'date': r[0], 'count': r[1], 'avg': round(r[2], 2), 'total': round(r[3], 2)} for r in daily],
                'weekly': [{'week': r[0], 'count': r[1], 'avg': round(r[2], 2), 'total': round(r[3], 2)} for r in weekly],
                'monthly': [{'month': r[0], 'count': r[1], 'avg': round(r[2], 2), 'total': round(r[3], 2)} for r in monthly]
            })
        except Exception as e:
            logger.error(f"Trends query failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @analytics_bp.route('/api/analytics/patterns')
    def get_patterns():
        """Get seasonal and day-of-week patterns"""
        try:
            # Day of week pattern
            day_of_week = db.execute_query('''
                SELECT CASE strftime('%w', prediction_date)
                    WHEN '0' THEN 'Sunday'
                    WHEN '1' THEN 'Monday'
                    WHEN '2' THEN 'Tuesday'
                    WHEN '3' THEN 'Wednesday'
                    WHEN '4' THEN 'Thursday'
                    WHEN '5' THEN 'Friday'
                    WHEN '6' THEN 'Saturday'
                END as day_name,
                strftime('%w', prediction_date) as day_num,
                AVG(predicted_weight_kg) as avg_weight,
                COUNT(*) as count
                FROM prediction_logs 
                GROUP BY day_num
                ORDER BY day_num
            ''', fetch_all=True)
            
            # Monthly pattern (seasonality)
            monthly_pattern = db.execute_query('''
                SELECT CASE strftime('%m', prediction_date)
                    WHEN '01' THEN 'Jan'
                    WHEN '02' THEN 'Feb'
                    WHEN '03' THEN 'Mar'
                    WHEN '04' THEN 'Apr'
                    WHEN '05' THEN 'May'
                    WHEN '06' THEN 'Jun'
                    WHEN '07' THEN 'Jul'
                    WHEN '08' THEN 'Aug'
                    WHEN '09' THEN 'Sep'
                    WHEN '10' THEN 'Oct'
                    WHEN '11' THEN 'Nov'
                    WHEN '12' THEN 'Dec'
                END as month_name,
                strftime('%m', prediction_date) as month_num,
                AVG(predicted_weight_kg) as avg_weight,
                COUNT(*) as count
                FROM prediction_logs 
                GROUP BY month_num
                ORDER BY month_num
            ''', fetch_all=True)
            
            return jsonify({
                'day_of_week': [{'day': r[0], 'avg': round(r[2], 2), 'count': r[3]} for r in day_of_week],
                'monthly': [{'month': r[0], 'avg': round(r[2], 2), 'count': r[3]} for r in monthly_pattern]
            })
        except Exception as e:
            logger.error(f"Patterns query failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @analytics_bp.route('/api/analytics/areas')
    def get_area_analysis():
        """Get area-wise analysis"""
        try:
            area_stats = db.execute_query('''
                SELECT area,
                       COUNT(*) as count,
                       AVG(predicted_weight_kg) as avg_weight,
                       MIN(predicted_weight_kg) as min_weight,
                       MAX(predicted_weight_kg) as max_weight,
                       SUM(predicted_weight_kg) as total_weight
                FROM prediction_logs 
                GROUP BY area
                ORDER BY total_weight DESC
            ''', fetch_all=True)
            
            return jsonify({
                'areas': [{
                    'area': r[0],
                    'count': r[1],
                    'avg': round(r[2], 2),
                    'min': round(r[3], 2),
                    'max': round(r[4], 2),
                    'total': round(r[5], 2)
                } for r in area_stats]
            })
        except Exception as e:
            logger.error(f"Area analysis failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @analytics_bp.route('/api/analytics/summary')
    def get_summary():
        """Get overall summary statistics"""
        try:
            summary = db.execute_query('''
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(predicted_weight_kg) as avg_weight,
                    MIN(predicted_weight_kg) as min_weight,
                    MAX(predicted_weight_kg) as max_weight,
                    SUM(predicted_weight_kg) as total_weight,
                    COUNT(DISTINCT area) as unique_areas,
                    COUNT(DISTINCT waste_type) as unique_waste_types
                FROM prediction_logs
            ''', fetch_one=True)
            
            return jsonify({
                'total_predictions': summary[0] or 0,
                'avg_weight': round(summary[1], 2) if summary[1] else 0,
                'min_weight': round(summary[2], 2) if summary[2] else 0,
                'max_weight': round(summary[3], 2) if summary[3] else 0,
                'total_weight': round(summary[4], 2) if summary[4] else 0,
                'unique_areas': summary[5] or 0,
                'unique_waste_types': summary[6] or 0
            })
        except Exception as e:
            logger.error(f"Summary query failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    app.register_blueprint(analytics_bp)
