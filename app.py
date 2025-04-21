from flask import Flask, request, send_file, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv, io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def scrape_domain(start_url):
    domain = urlparse(start_url).netloc
    visited, to_visit, data = set(), [start_url], []
    while to_visit:
        url = to_visit.pop(0)
        if url in visited: continue
        visited.add(url)
        try:
            resp = requests.get(url); resp.raise_for_status()
        except:
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else ''
        content = soup.get_text(separator=' ', strip=True)
        data.append({'url': url, 'title': title, 'content': content})
        for a in soup.find_all('a', href=True):
            full = urljoin(start_url, a['href'])
            if urlparse(full).netloc == domain and full not in visited:
                to_visit.append(full)
    return data

@app.route('/scrape', methods=['POST'])
def scrape():
    js = request.get_json() or {}
    url = js.get('url')
    if not url:
        return jsonify({'error':'No URL provided'}), 400
    rows = scrape_domain(url)
    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=['url','title','content'])
    writer.writeheader(); writer.writerows(rows)
    mem = io.BytesIO(); mem.write(si.getvalue().encode()); mem.seek(0); si.close()
    return send_file(mem,
                 mimetype='text/csv',
                 as_attachment=True,
                 download_name='scraped_data.csv')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
