class BigQueryClient():
    def __init__(self, credential_json):
        from google.oauth2 import service_account
        self.credentials = service_account.Credentials.from_service_account_file(credential_json)

    def query(self, query_str):
        import pandas as pd
        return pd.read_gbq(query_str, credentials=self.credentials)


class ImageHandler():
    def resnet_extractor(self, image_shape, include_top=False,weights='imagenet'):
        from keras.layers import Input
        from tensorflow.keras.applications.resnet50 import ResNet50
        return ResNet50(include_top, weights, input_tensor=Input(shape=image_shape))

    def get_feature(self, clf, img):
        feature_vector = clf.predict(img)
        a, b, c, n = feature_vector.shape
        feature_vector= feature_vector.reshape(b,n)
        return feature_vector


    def load_img(self, path, grayscale=False, target_size=(224, 224)):
        import requests
        from PIL import Image
        from io import BytesIO

        try:
            from PIL import Image as pil_image
        except ImportError:
            pil_image = None

        if pil_image is None:
            raise ImportError('Could not import PIL.Image. '
                            'The use of `array_to_img` requires PIL.')

        response = requests.get(path)
        img = Image.open(BytesIO(response.content))
        #img = pil_image.open(path)
        if grayscale:
            if img.mode != 'L':
                img = img.convert('L')
        else:
            if img.mode != 'RGB':
                img = img.convert('RGB')
        if target_size:
            hw_tuple = (target_size[1], target_size[0])
            if img.size != hw_tuple:
                img = img.resize(hw_tuple)
        return img

    

if __name__ == '__main__':
    pass