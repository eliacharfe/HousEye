from singletonDecorator import singleton
import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
"""
This class represents a DataBase that holds all the information about coins that founds by the program.
"""


@singleton
class Database:
    def __init__(self):
        self.cred = credentials.Certificate("./ServiceAccountKey.json")
        firebase_admin.initialize_app(self.cred, {
            'storageBucket': 'houseeye-ea111.appspot.com'
        })

        self.db = firestore.client()
        self.bucket = storage.bucket()

    def add_user(self,user_name, image_path):
        """
        Add new user to database.
        :param user_name: The username of the user
        :param image_path: Image path for the image
        :return:
        """
        try:
            if not self.db.collection('Users').where('username', '==', user_name).get():
                self.db.collection('Users').add({'username': user_name, 'image': image_path})
            else:
                return "User is already inside"
        except Exception as e:
            return e.args
        return "Successfully Added"

    def delete_user(self, user_name,image_path):
        """
        Delete user from database.
        :param user_name: The user name you want to delete
        :return str:
        """
        try:
            query_ref = self.db.collection('Users').where('username', '==', user_name).get()
            for doc in query_ref:
                doc_id = doc.id
                self.db.collection("Users").document(doc_id).delete()
            blob = self.bucket.blob(image_path)
            blob.delete()
        except Exception as e:
            return e.args
        return "Successfully Deleted"

    def get_user(self, user_name):
        """
        Get username.
        :param user_name: The username you need.
        :return: username
        """
        try:
            query_ref = self.db.collection('Users').where('username', '==', user_name).get()
            doc = query_ref[0].to_dict()

        except Exception as e:
            return e.args
        return doc

    def add_image(self, image_file):
        """
        Add image
        :param user_name: The user who own the image
        :param image_file: Image to upload
        :return:
        """
        try:
            blob = self.bucket.blob(image_file)
            blob.upload_from_filename(image_file)
        except Exception as e:
            return e.args
        return "Successfully Added"

    def delete_image(self, image_file):
        """
        Delete image.
        :param image_file: Image to delete
        :return:
        """
        try:
            blob = self.bucket.blob(image_file)
            blob.delete()
        except Exception as e:
            return e.args
        return "Successfully Added"

    def find_user_by_image(self, image_path):
        """
        Get username by image.
        :param image_path: Image of user
        :return: username
        """
        try:
            query_ref = self.db.collection('Users').where('image_path', '==', image_path)
            doc = query_ref[0].to_dict()
        except Exception as e:
            return e.args
        return doc