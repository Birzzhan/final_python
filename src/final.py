from datetime import datetime, timedelta
from flask import Flask , redirect, url_for,render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
from transformers import pipeline

app = Flask(__name__,template_folder='template')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:zf9392zf@localhost/pythonDB'
db = SQLAlchemy(app)
class Example(db.Model):
    __tablename__ = 'coins'
    id = db.Column('id', db.Integer, primary_key=True)
    data = db.Column('data', db.Unicode)
    def __init__(self, id, data):
        self.id = id
        self.data = data


def summ(link):
    summarizer = pipeline("summarization")
    r = requests.get(link)
    soup = BeautifulSoup(r.text, 'lxml')
    results = soup.find_all(['h1', 'p'])
    text = [result.text for result in results]
    ARTICLE = ' '.join(text)
    ARTICLE = ARTICLE.replace('.', '.<eos>')
    ARTICLE = ARTICLE.replace('?', '?<eos>')
    ARTICLE = ARTICLE.replace('!', '!<eos>')
    max_chunk = 500
    sentences = ARTICLE.split('<eos>')
    current_chunk = 0
    chunks = []
    for sentence in sentences:
        if len(chunks) == current_chunk + 1:
            if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
                chunks[current_chunk].extend(sentence.split(' '))
            else:
                current_chunk += 1
                chunks.append(sentence.split(' '))
        else:
            print(current_chunk)
            chunks.append(sentence.split(' '))

    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = ' '.join(chunks[chunk_id])

    res = summarizer(chunks, max_length=30, min_length=10, do_sample=False)
    text = ' '.join([summ['summary_text'] for summ in res])
    return text

@app.route('/' ,methods = ["POST","GET"])
def login():
    if request.method == "POST":
        user = request.form["coin"]
        return redirect(url_for("user",usr = user))
    else:
        return render_template("form.html")

@app.route("/<usr>")
def user(usr):


    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
    url = "https://www.google.com/search?q=site:https://coinmarketcap.com/+" + usr + "+eng"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    i = 1
    for g in soup.find_all('h3'):
        new_ex = Example(i,g.text)
        db.session.add(new_ex)
        db.session.commit()
        i=i+1

    titless = soup.find_all('h3')
    titles = soup.find_all('div', {'class': 'yuRUbf'})
    url_list = []
    for item in titles:
        temp = item.find('a').get('href').replace('ru/', '')
        url_list.append(temp[:25] + '/en' + temp[25:])

    strTitles = []
    j = 0
    for h3 in titless[:3]:
        strTitles.append(f'<div class = "article"><a href = "{url_list[j]}">{str(h3)}</a><p>{summ(url_list[j]).replace(",", "，")}.</p></div>')
        j+=1

    return render_template("form.html") + str(strTitles).translate({ord(c):None for c in "[],'"})
        

if __name__ == '__main__':
    app.run(debug=True)
