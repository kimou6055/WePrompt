<img  width='805' src="https://miro.medium.com/v2/resize:fit:1400/1*iGdFJTHMIG79N2HChWaooQ.gif" alt="kimou6055" /></a> 


## WePromt 2.0
WePrompt is a GUI that helps you with SQL queries , and debbuging at Wevioo !

## Prerequirments
Python 3.4+
Virtualenv
pip

## Installation

```
git clone https://github.com/kimou6055/WePrompt.git
```
All of the following will be built into a virtualenv

open the cmd in the root folder
do : 
```
cd ../

```

Then do the follow:

```
python3 -m venv myenv
```

Then activate the environnement

windows : 
```
myenv\Scripts\activate
```


linux : 
```
source myenv/bin/activate
```
Make sure you have Python 3.x installed on your machine. You can install the required Python libraries by running:

```
pip install rwkv
pip install torch
pip install pynvml
pip install fastapi
pip install pydantic
pip install mysql
pip install pickle


```
you can dowload the RAVEN V12 7B Params from this [Link](https://cdn-lfs.huggingface.co/repos/41/55/4155c7aaff64e0f4b926df1a8fff201f8ee3653c39ba67b31e4973ae97828633/5a725eaeb9e09b724de6c97e6845dd0283097c7920acd05b46852ab7afa9ec32?response-content-disposition=attachment%3B+filename*%3DUTF-8%27%27RWKV-4-Raven-7B-v12-Eng98%2525-Other2%2525-20230521-ctx8192.pth%3B+filename%3D%22RWKV-4-Raven-7B-v12-Eng98%25-Other2%25-20230521-ctx8192.pth%22%3B&Expires=1686839760&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9jZG4tbGZzLmh1Z2dpbmdmYWNlLmNvL3JlcG9zLzQxLzU1LzQxNTVjN2FhZmY2NGUwZjRiOTI2ZGYxYThmZmYyMDFmOGVlMzY1M2MzOWJhNjdiMzFlNDk3M2FlOTc4Mjg2MzMvNWE3MjVlYWViOWUwOWI3MjRkZTZjOTdlNjg0NWRkMDI4MzA5N2M3OTIwYWNkMDViNDY4NTJhYjdhZmE5ZWMzMj9yZXNwb25zZS1jb250ZW50LWRpc3Bvc2l0aW9uPSoiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE2ODY4Mzk3NjB9fX1dfQ__&Signature=0Jwur-Ougikh7SokGmHaSKXuKRCbZZ3KwtmYOHXtv33qv5aBH5SmetcMKbv8eaCoJ8LPkcnnMjV8b2gBGDJ50jsrW6nyDaGHg0jtAq%7EzABdckKVHR5M46Aa857QZU-W1e-8Q8rabnLgYeADLIDfpRPIIjkgc8sv4dxI7PaK4Q-03Zfju7d8Cnr9%7EMjCQ9BrBXZcvnyQaEChGrCSeg9yt8eR6B5Usg4wU2uYxnqSykDQzXSVhR%7EQNg4cuz0sRZjN57IUSnULjKTJaaIHYFEvhwzzBb-uUnqfQRy11G46nTmw9LTeEJqcwagVUMzSiniFeXHMZ%7EwoQtc6CqDaogDCKwA__&Key-Pair-Id=KVTP0A1DKRTAX)

Make sure to put the model in the root folder

## Usage
To use just do : 

```
cd instructions
```

```
python RavenApi2.0.py
```

To use it as a FastApi: 

```
python RavenApi.py
```
Then send a POST request at this address: http://localhost:8000/generate-response

in this syntax : 
```
{
  "user_message": " summarize our last conversation  ",
  "user_id": "22",
  "discussion_id": "4",
  "prompt_file": "ProjectAdvisor"
}

```
the response will be as the follow : 
```
{
    "generated_text": " Sure, here's a summary of our conversation:\n1. I created a new file called `Home.js` and added some basic HTML and CSS to it.\n2. I created a new file called `index.js` and added some basic code to it, including a function that sends a request to the MySQL database using the `axios` library.\n3. I created a new file called `App.js` and added some basic code to it, including a function that renders the Home component using the `ReactDOM.render()` method.\n4. I created a new file called `index.css` and added some basic styles to it, including a logo and some basic styling for the page\n\n"
}
```
You can use ProjectAdvisor or SQLAdvisor at the moment
## TO DO 

Consuming the API with Joget
