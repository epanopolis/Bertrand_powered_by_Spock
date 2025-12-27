"""
The I/O for language processing and code interpretation. Spock's engine.

"""
from flask import Blueprint, request, jsonify
from bertrand.language_services import Chomsky

bp = Blueprint('spock', __name__)

def process_string(input_string):
    """
    Process the input string to handle encoding and decode UTF-8 characters 
    properly.
    
    """
    if not input_string:
        return {'success': False, 'message': "Input text cannot be empty."}, 400

    processed_content = []
    input_bytes = input_string.encode('utf-8', errors='surrogateescape') \
        if isinstance(input_string, str) else input_string

    i = 0
    while i < len(input_bytes):
        try:
            char = input_bytes[i:i+1].decode("utf-8")
            processed_content.append(char)
            i += 1
        except UnicodeDecodeError:
            try:
                char = input_bytes[i:i+2].decode("utf-8")
                processed_content.append(char)
                i += 2
            except UnicodeDecodeError:
                try:
                    char = input_bytes[i:i+3].decode("utf-8")
                    processed_content.append(char)
                    i += 3
                except UnicodeDecodeError:
                    processed_content.append(f"[UNDECODABLE:{input_bytes[i]}]")
                    i += 1

    processed_source = ''.join(processed_content)
    processed_source += "$$" # Add the EOF characters
    return processed_source

@bp.route('/analysis', methods=['POST'])
def analysis_route():
    """
    Handles POST requests to the /analysis endpoint.
    Extracts textInput, processes it, and generates a conclusion report.
    
    """
    try:
        input_string = request.form.get('textInput', '')
        if not input_string:
            return jsonify({'success': False, 'message': \
                'Input text cannot be empty.'}), 400

        source = process_string(input_string)

        result = Chomsky.chomsky(source)

        return jsonify({
            'success': True,
            'message': 'Analysis completed successfully.',
            'conclusion': result
        })

    except RuntimeError as e:
        return jsonify({'success': False, 'message': f"""Error processing input:
            {str(e)}"""}), 500
