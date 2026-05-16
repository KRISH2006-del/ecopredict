# Export functionality for predictions (CSV and PDF)

import io
import csv
from datetime import datetime
from flask import Blueprint, Response, make_response, session
import logging

logger = logging.getLogger(__name__)

exports_bp = Blueprint('exports', __name__)


def register_export_routes(app, db):
    """Register export routes"""
    
    @exports_bp.route('/export/csv')
    def export_csv():
        """Export prediction history as CSV"""
        user_id = session.get('user_id')
        
        try:
            if user_id:
                # Get user-specific predictions
                rows = db.execute_query(
                    '''SELECT prediction_date, area, waste_type, predicted_weight_kg, timestamp 
                       FROM prediction_logs WHERE user_id = ? ORDER BY id DESC''',
                    (user_id,),
                    fetch_all=True
                )
            else:
                # Get all predictions (limited)
                rows = db.execute_query(
                    '''SELECT prediction_date, area, waste_type, predicted_weight_kg, timestamp 
                       FROM prediction_logs ORDER BY id DESC LIMIT 100''',
                    fetch_all=True
                )
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Prediction Date', 'Area', 'Waste Type', 'Predicted Weight (kg)', 'Timestamp'])
            
            # Data rows
            for row in rows:
                writer.writerow(row)
            
            # Create response
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'waste_predictions_{timestamp}.csv'
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return {'error': 'Export failed'}, 500
    
    @exports_bp.route('/export/pdf')
    def export_pdf():
        """Export prediction history as PDF (simple HTML-based)"""
        user_id = session.get('user_id')
        
        try:
            if user_id:
                rows = db.execute_query(
                    '''SELECT prediction_date, area, waste_type, predicted_weight_kg, timestamp 
                       FROM prediction_logs WHERE user_id = ? ORDER BY id DESC LIMIT 50''',
                    (user_id,),
                    fetch_all=True
                )
            else:
                rows = db.execute_query(
                    '''SELECT prediction_date, area, waste_type, predicted_weight_kg, timestamp 
                       FROM prediction_logs ORDER BY id DESC LIMIT 50''',
                    fetch_all=True
                )
            
            # Generate simple HTML report for printing
            html = generate_pdf_html(rows)
            
            return Response(
                html,
                mimetype='text/html',
                headers={'Content-Disposition': 'attachment; filename=waste_predictions_report.html'}
            )
            
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return {'error': 'Export failed'}, 500
    
    @exports_bp.route('/export/json')
    def export_json():
        """Export prediction data as JSON"""
        user_id = session.get('user_id')
        
        try:
            if user_id:
                rows = db.execute_query(
                    '''SELECT prediction_date, area, waste_type, predicted_weight_kg, timestamp 
                       FROM prediction_logs WHERE user_id = ? ORDER BY id DESC''',
                    (user_id,),
                    fetch_all=True
                )
            else:
                rows = db.execute_query(
                    '''SELECT prediction_date, area, waste_type, predicted_weight_kg, timestamp 
                       FROM prediction_logs ORDER BY id DESC LIMIT 100''',
                    fetch_all=True
                )
            
            data = [{
                'prediction_date': row[0],
                'area': row[1],
                'waste_type': row[2],
                'predicted_weight_kg': row[3],
                'timestamp': row[4]
            } for row in rows]
            
            return {'predictions': data, 'count': len(data)}
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return {'error': 'Export failed'}, 500
    
    app.register_blueprint(exports_bp)


def generate_pdf_html(rows):
    """Generate printable HTML report"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    rows_html = ''
    for row in rows:
        rows_html += f'''
        <tr>
            <td>{row[0]}</td>
            <td>{row[1]}</td>
            <td>{row[2]}</td>
            <td>{row[3]:.2f} kg</td>
            <td>{row[4]}</td>
        </tr>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Waste Prediction Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            h1 {{ color: #27ae60; border-bottom: 3px solid #27ae60; padding-bottom: 10px; }}
            .meta {{ color: #666; margin-bottom: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background: #27ae60; color: white; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            tr:hover {{ background: #f1f1f1; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            @media print {{
                body {{ margin: 20px; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <h1>Waste Prediction Report</h1>
        <p class="meta">Generated on: {timestamp}</p>
        <p class="meta">Total Records: {len(rows)}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Prediction Date</th>
                    <th>Area</th>
                    <th>Waste Type</th>
                    <th>Predicted Weight</th>
                    <th>Created At</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        
        <div class="footer">
            <p>EcoPredict Systems - Waste Management Intelligence</p>
        </div>
        
        <script class="no-print">window.print();</script>
    </body>
    </html>
    '''
