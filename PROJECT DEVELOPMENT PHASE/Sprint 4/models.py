import numpy as np
import sqlite3
from keras.models import load_model
from keras.utils import load_img,img_to_array

def predict(filepath,genus):
    conn = sqlite3.connect("Species_data.db")
    model = load_model(models(genus))
    img = load_img(filepath,target_size=(229,229))
    x = img_to_array(img)
    x = np.expand_dims(x,axis=0)
    pred = np.argmax(model.predict(x))
    cursor = conn.execute(f'''SELECT GENUS,CONTENT FROM SPECIESDB WHERE SPECIES=="{genus}" AND ID=="{pred}"''')
    val = cursor.fetchall()[0]
    genus_value = val[0]
    content = val[1]
    return [genus_value,content]

def models(classes):
    if classes == "Animals":
        return 'models/animals.h5'
    elif classes == "Birds":
        return 'models/birds.h5'
    elif classes == "Leaves":
        return 'models/leaves.h5'
    elif classes == "Flowers":
        return 'models/flowers.h5'
    elif classes == "Insects":
        return 'models/insects.h5'
    elif classes == "Sea Animals":
        return 'models/sea.h5'

