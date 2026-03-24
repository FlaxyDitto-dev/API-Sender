from flask import Flask, request, jsonify, render_template_string
import requests
import os
import time
import base64

app = Flask(__name__)

# --- The Frontend HTML/JS UI ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Web API Sender</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }
        .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 700px; margin: auto; }
        .row { margin-bottom: 15px; }
        button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; border-radius: 4px; }
        button:hover { background-color: #45a049; }
        button.remove { background-color: #f44336; padding: 6px 10px; margin-left: 5px; }
        button.remove:hover { background-color: #da190b; }
        input[type="text"] { padding: 8px; width: 220px; border: 1px solid #ccc; border-radius: 4px; }
        #url { width: 100%; box-sizing: border-box; }
        #result { width: 100%; height: 250px; margin-top: 10px; padding: 10px; box-sizing: border-box; font-family: monospace; border: 1px solid #ccc; border-radius: 4px;}
        #media-result { display: none; margin-top: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 4px; background: #fafafa; text-align: center; }
        #media-result img, #media-result video { max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .var-row { display: flex; align-items: center; margin-bottom: 5px; gap: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Web API Sender</h2>
        
        <div class="row">
            <label><b>Target URL:</b></label><br>
            <input type="text" id="url" placeholder="http://127.0.0.1:8080/api">
        </div>

        <div class="row">
            <label><b>Payload Variables:</b></label>
            <div id="variables">
                <div class="var-row">
                    <input type="text" placeholder="Variable (Key)" class="v-key">
                    <input type="text" placeholder="Data (Value)" class="v-val">
                    <button class="remove" onclick="this.parentElement.remove()">X</button>
                </div>
            </div>
            <button onclick="addVar()" style="margin-top: 5px; background-color: #2196F3;">+ Add Variable</button>
        </div>

        <div class="row" style="display: flex; gap: 20px; align-items: center;">
            <label><input type="checkbox" id="is_json" checked> Send as JSON format</label>
            <label><input type="checkbox" id="save_file"> Save result to a file (on server)</label>
        </div>

        <button onclick="sendReq()" style="font-size: 16px; font-weight: bold; width: 100%;">SEND REQUEST</button>

        <div class="row" style="margin-top: 20px;">
            <label><b>Result:</b></label>
            <textarea id="result" readonly placeholder="Awaiting request..."></textarea>
            
            <div id="media-result"></div>
        </div>
    </div>

    <script>
        function addVar() {
            const div = document.createElement('div');
            div.className = 'var-row';
            div.innerHTML = `<input type="text" placeholder="Variable (Key)" class="v-key">
                             <input type="text" placeholder="Data (Value)" class="v-val">
                             <button class="remove" onclick="this.parentElement.remove()">X</button>`;
            document.getElementById('variables').appendChild(div);
        }

        async function sendReq() {
            const url = document.getElementById('url').value;
            const is_json = document.getElementById('is_json').checked;
            const save_file = document.getElementById('save_file').checked;
            
            const textResultBox = document.getElementById('result');
            const mediaResultBox = document.getElementById('media-result');

            if(!url) {
                alert("Please enter a Target URL.");
                return;
            }

            // Gather variables
            const keys = document.querySelectorAll('.v-key');
            const vals = document.querySelectorAll('.v-val');
            let payload = {};
            for(let i=0; i<keys.length; i++) {
                if(keys[i].value.trim() !== '') {
                    payload[keys[i].value.trim()] = vals[i].value.trim();
                }
            }

            // Reset UI
            textResultBox.style.display = 'block';
            mediaResultBox.style.display = 'none';
            mediaResultBox.innerHTML = '';
            textResultBox.value = "Sending request...";

            try {
                const res = await fetch('/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ target_url: url, payload: payload, is_json: is_json, save_file: save_file })
                });
                
                const data = await res.json();
                
                if (data.type === 'media') {
                    // Hide text area, show media area
                    textResultBox.style.display = 'none';
                    mediaResultBox.style.display = 'block';
                    
                    // Add status code info
                    let statusHtml = `<p style="text-align: left; margin-top: 0; font-family: monospace;">Status Code: ${data.status_code}<br>Content-Type: ${data.mime_type}`;
                    if (data.saved_to) {
                        statusHtml += `<br>Saved to: ${data.saved_to}`;
                    }
                    statusHtml += `</p><hr>`;
                    mediaResultBox.innerHTML = statusHtml;

                    // Create the appropriate media element
                    let mediaElem;
                    const srcData = `data:${data.mime_type};base64,${data.data}`;
                    
                    if (data.mime_type.startsWith('image/')) {
                        mediaElem = document.createElement('img');
                    } else if (data.mime_type.startsWith('video/')) {
                        mediaElem = document.createElement('video');
                        mediaElem.controls = true;
                    } else if (data.mime_type.startsWith('audio/')) {
                        mediaElem = document.createElement('audio');
                        mediaElem.controls = true;
                    }

                    mediaElem.src = srcData;
                    mediaResultBox.appendChild(mediaElem);

                } else {
                    // Handle standard text/json response
                    let output = `Status Code: ${data.status_code}\\n`;
                    if (data.mime_type) {
                        output += `Content-Type: ${data.mime_type}\\n`;
                    }
                    output += "----------------------------------------\\n";
                    if (data.saved_to) {
                        output += `--- Result saved on Host Machine to:\\n${data.saved_to} ---\\n\\n`;
                    }
                    output += data.data; // The actual text/json
                    textResultBox.value = output;
                }

            } catch (err) {
                textResultBox.style.display = 'block';
                mediaResultBox.style.display = 'none';
                textResultBox.value = "Failed to communicate with the Python server.\\n" + err;
            }
        }
    </script>
</body>
</html>
"""

# --- The Backend Logic ---

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/send', methods=['POST'])
def send_request():
    data = request.json
    target_url = data.get('target_url', '').strip()
    payload = data.get('payload', {})
    is_json = data.get('is_json', True)
    save_file = data.get('save_file', False)

    if not target_url.startswith("http"):
        target_url = "http://" + target_url

    try:
        # Make the actual request to the target
        if is_json:
            resp = requests.post(target_url, json=payload)
        else:
            resp = requests.post(target_url, data=payload)
        
        content_type = resp.headers.get('Content-Type', '').lower()
        saved_path = None

        # Determine if the response is media (image, video, audio)
        is_media = content_type.startswith(('image/', 'video/', 'audio/'))

        # Handle saving to file on the host machine
        if save_file:
            # Guess the extension based on content type, default to .json or .bin
            ext = ".bin"
            if is_media:
                ext = "." + content_type.split('/')[-1].split(';')[0] # e.g., 'image/png' -> '.png'
            elif "json" in content_type:
                ext = ".json"
            elif "text" in content_type:
                ext = ".txt"

            filename = f"api_result_{int(time.time())}{ext}"
            filepath = os.path.abspath(filename)
            
            # Write bytes if media, otherwise write text
            mode = "wb" if is_media else "w"
            encoding = None if is_media else "utf-8"
            
            with open(filepath, mode, encoding=encoding) as f:
                if is_media:
                    f.write(resp.content)
                else:
                    f.write(resp.text)
            saved_path = filepath

        # Prepare the response to send back to the web browser
        if is_media:
            # Encode binary data to Base64 so it can be sent via JSON safely
            encoded_media = base64.b64encode(resp.content).decode('utf-8')
            return jsonify({
                "status_code": resp.status_code,
                "type": "media",
                "mime_type": content_type,
                "data": encoded_media,
                "saved_to": saved_path
            })
        else:
            # Standard text/json response
            return jsonify({
                "status_code": resp.status_code,
                "type": "text",
                "mime_type": content_type,
                "data": resp.text,
                "saved_to": saved_path
            })

    except Exception as e:
        return jsonify({
            "status_code": "Error",
            "type": "text",
            "data": str(e)
        })

if __name__ == "__main__":
    print("Starting Web API Sender...")
    app.run(host="0.0.0.0", port=5000) # Changed from 1000 to 5000