import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["service_account"],
        "project_id": st.secrets["sevasetu-70378"],
        "private_key_id": st.secrets["55818c7b83d0ea89383c2ab967b047b2606b1975"],
        "private_key": st.secrets["-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCx9SFjUmujKhDy\n/iA6UVJPgi5I6v38KJtYc7TmrEFH4e0Ze0yXHa8309JNNxHL4tG1QjCqijMuvS3c\nXs3wZ5D0lB/qpnCHm4Zr9+NJ2vanu8/F1iwOEvcha70VTp4rfqq3Y0hV8iC7zJK4\nTvuizjh0NbTWrZvK4GP7O8Xn8F+qQ0Cv25X15RCN2CX6O8a+1Dxj2DZNBLRTmIpM\nhrWlW545MQjk23u0q+DhMHAnCDmFGh8tKu9RavUIzg7p3ftTb/LQ0FDHSBE6eNW9\nHcMOmcFSRyUs4baVhQLKQeF7wvUJdlPl/pV4SAfJZZUxdYNUSFKKzzYOcuQwjOBg\nA+gaQEHjAgMBAAECggEAAnQxxpFWrtRmXgg3QI0DhT/AMwnOgJSJkKT6NYR79MMY\nRmKTxUrhZVphF+bhzD2iv6ZogZZQEcQF2fgsTDU/yfRkiXmyRPE8X5Vc+uII+a1W\naZ3dukBa5dXHymXs1DocarsoC0tZ75nPQh+QsVRS2Fz8Bko0ww21QzvpRQMxbOl+\nAhQZdHG1HTBmPs13HCJiXYO2Egb/fTYc72i1yUAmlMEJWoFZJIMNOql6fgj90NcF\nKRf3/mnsj4R2wSBNN8if330PhpzwwF3wpzkdPH5NnfIOrrsHP2CJSCJ7VxcrXYzd\n8mxLTp6Mg2y2w4nk/gU23cnVHklPZjLvehHwSwy0hQKBgQDYfKeURi5tIBHw1H4D\n6yChUOneexFJq6V1kIjmJ79TMFVsbyLYgjlox0Kws78RiEKqwZq3oU0pk+6X8RCQ\nW5GU7ofcw/s41JgJS8QsRo1Hn9eVOg6iYAEmfHvYWdfRKH25kP7KQ14imE7BnNfM\nMe2t8kCnVH1en3UFeOJBmiN8/wKBgQDScDDwDdRlBfLJPt18HtQ9XYZ39iJ2+d+b\nQfhQ9e/3CnBxurpLlwNa62l4FpnnpVrIfmSnFBvur059djkNPC8HXdcUnJeraTkl\n2ziKrukeftRYZpkRxXRDdEgYuIHixogrfMnSB6hyyFMVV91GTLPZ/k+yIYvkCbt0\nwCXTNI/nHQKBgQCktGo26BJIWf7sUG6zgn8n3EyiRNWJTDstL9LH8HOi0gIb5o4H\nVURiUD+P+qEisJ2wFm4kyWbQfEkpdnGYsuIXAkeBkeWffjdR00AkQ2UXmifF1A7w\nQMR/SHRczTXiXsEQnp0Ku6hx/5jjuvV/2HixP78qz6A2jnDUwfy51pCrdwKBgBHa\nYsx63+ISNx7Lro6xLuBl5tqWjyX43PeXCTIVK16SDCgZ52QyU56LCk+d20DDzofj\n8TYbhqMhTE9okD6HNJYzZ+PfxR5NtwN3LbzWSgDEUc+OJL5VOh/e5Z7zSFGs9jB6\nTcT70VarmCDfa25jY37DDI/YOL4H9VdaVdstQmghAoGAEbFgoT1PLPu7eg9irbQX\nPFWeqZbxZ8SnlVlpWFGBfOxG0m0ejy9R2/gVygQ0RS0+97SejlirycifMLDgyUn5\nRwOnN/RZPCw5n3zD50gqBKOZbqnoadNaOv8qiLTZy85Ndj8WuuF8WdxQZMYhNcfS\nUIM8tshkJ2EPu90d8jPHAmw=\n-----END PRIVATE KEY-----\n"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase-adminsdk-fbsvc@sevasetu-70378.iam.gserviceaccount.com"],
        "client_id": st.secrets["109673586445428059476"],
        "auth_uri": st.secrets["https://accounts.google.com/o/oauth2/auth"],
        "token_uri": st.secrets["https://oauth2.googleapis.com/token"],
        "auth_provider_x509_cert_url": st.secrets["https://www.googleapis.com/oauth2/v1/certs"],
        "client_x509_cert_url": st.secrets["https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40sevasetu-70378.iam.gserviceaccount.com"]
    })
    firebase_admin.initialize_app(cred, {
        "databaseURL": st.secrets["https://sevasetu-70378-default-rtdb.firebaseio.com"]
    })

root = db.reference("/")