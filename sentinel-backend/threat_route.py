from flask import Blueprint, request, jsonify, current_app
import os

threat_bp = Blueprint('threat', __name__)

@threat_bp.route("/api/analyze_threat", methods=["POST"])
def analyze_threat():
    """Full threat analysis of rumor with generated comments"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No rumor text provided"}), 400
            
        # Get components
        comment_gen = current_app.config.get('COMMENT_GENERATOR')
        threat_scorer = current_app.config.get('THREAT_SCORER')
        
        if not comment_gen or not threat_scorer:
            return jsonify({
                "error": "Required components not initialized"
            }), 500
            
        # Generate sample comments
        try:
            comments = comment_gen.generate_thread(data['text'])
        except Exception as e:
            print(f"Comment generation failed: {e}")
            comments = []
            
        # Full threat analysis
        try:
            threat_analysis = threat_scorer.analyze_thread(
                data['text'],
                comments,
                factcheck_api_key=os.getenv('GOOGLE_FACTCHECK_API_KEY')
            )
        except Exception as e:
            print(f"Threat analysis failed: {e}")
            return jsonify({
                "error": "Threat analysis failed",
                "details": str(e)
            }), 500
            
        # Build response
        response = {
            "rumor": data['text'],
            "threat_analysis": threat_analysis,
            "generated_comments": comments[:5],  # Sample of comments
            "comment_count": len(comments)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Analysis failed: {str(e)}"
        }), 500