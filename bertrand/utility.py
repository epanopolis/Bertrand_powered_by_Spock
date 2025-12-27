"""
Helper functions for javascript interface to Python structure and Spock's I/O.  
Handles user requests and routing for those functions.

"""
import os
import sys
from flask import Blueprint, request, jsonify, current_app
from flask import render_template, make_response
from werkzeug.utils import secure_filename
from bertrand import spock

bp = Blueprint('utility', __name__)
""" Builds routes to this module. """

@bp.route("/", methods=['GET', 'POST'])
def input_screen():
    """ The route to the home template. """
    return render_template('utility/index.html')

@bp.route('/save_text', methods=['POST'])
def save_text():
    """ Function for saving downloaded text """
    data = request.form.get('textInput', '')
    if not data:
        return jsonify(success=False, message="No text input provided"), 400

    try:
        # Process the content as needed
        processed_content = spock.process_string(data)

        # Return the processed content as JSON
        return jsonify({
            'success': True,
            'message': 'Text processed successfully.',
            'processed_content': processed_content
        })
    except RuntimeError as e:
        return jsonify(success=False, message=f"""Failed to process text:
            {str(e)}"""), 500

def allowed_file(file):
    """
    Limits files to txt files and less than one megabyte in size.

    """
    try:
        # Validate file type
        if ('.' not in file.filename or file.filename.rsplit('.', 1)[1].lower()
            != 'txt'):
            return False, jsonify({'success': False, 'message':
                "Invalid file type. Only .txt files are allowed."})

        # Check file size
        file.seek(0, os.SEEK_END)  # Move to end of file to get size
        if file.tell() > current_app.config['MAX_CONTENT_LENGTH']:
            return False, jsonify({'success': False, 'message':
                "The file is too large."})

        file.seek(0)  # Reset file pointer
        return True, None  # Always return a tuple (True, None) for valid files
    except RuntimeError as e:
        return False, jsonify({'success': False, 'message':
            "File validation error: " + str(e)})

@bp.route('/upload', methods=['POST'])
def upload():
    """Function for uploading text input."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': "No file uploaded."})

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'message': "No file selected."})

        valid, error_msg = allowed_file(file)
        if not valid:
            return error_msg # Return the error message JSON if validation fails

        filename = secure_filename(file.filename)
        save_path = os.path.join('/tmp', filename)
        file.save(save_path)
        return jsonify({'success': True, 'message':
            "File uploaded successfully!"})

    except RuntimeError as e:
        return jsonify({'success': False, 'message':
            f"An error occurred: {str(e)}"})

@bp.route('/download', methods=['POST'])
def download():
    """ Function for downloading data"""
    try:
        # pull text from either 'textInput' or 'reportContent'
        text_data = (request.form.get('textInput')
                     or request.form.get('reportContent')
                     or '')

        if not text_data.strip():
            return jsonify({'success': False, 'message':
                "No text provided to save."}), 400

        response = make_response(text_data)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = \
            'attachment; filename="downloaded_text.txt"'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Content-Length'] = str(len(text_data.encode('utf-8')))
        return response

    except RuntimeError as e:
        print(">>> ERROR in /download:", str(e), file=sys.stderr)
        return jsonify({'success': False,
            'message': f"An error occurred: {str(e)}"}), 500
