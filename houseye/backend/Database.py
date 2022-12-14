from datetime import datetime
from typing import List, Dict, Any, Union

from google.api_core.page_iterator import Iterator
from google.cloud.storage import Blob

from singletonDecorator import singleton
import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage


@singleton
class Database:
    """Connection between server to cloud database."""
    def __init__(self):
        self.cred = credentials.Certificate("backend/ServiceAccountKey.json")
        firebase_admin.initialize_app(self.cred, {
            'storageBucket': 'houseeye-ea111.appspot.com'
        })

        self.db = firestore.client()
        self.bucket = storage.bucket()

    def add_user(self, user_name, cellphone, image_path):
        """
        Add new user to database.
        :param user_name: The username of the user
        :param image_path: Image path for the image
        :param cellphone: The cellphone of the user.
        :return:
        """
        try:
            if not self.db.collection('Users').where('username', '==', user_name).get():
                self.db.collection('Users').add({'username': user_name,
                                                 'cellphone': cellphone,
                                                 'image': image_path,
                                                 'status': 'Out'})
            else:
                return "User is already inside"
        except Exception as e:
            return e.args
        return "Successfully Added"

    def delete_user(self, user_name, image_path):
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

    def get_cellphones(self):
        """
        Get all cellphone numbers in the database.
        :return: List of cellphones.
        """
        return [user['cellphone'] for user in self.get_all_users()]

    def get_user(self, user_name):
        """
        Get username.
        :param user_name: The username you need.
        :return: username
        """
        try:
            query_ref = self.db.collection('Users').where('username', '==', user_name).get()
            doc = query_ref[0].to_dict()['username']
            return doc
        except Exception as e:
            return False

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
            query_ref = self.db.collection('Users').where('image', '==', image_path).get()
            username = query_ref[0].to_dict()['username']
        except Exception as e:
            return e.args
        return username

    def find_cell_by_user(self, username: str) -> Union[tuple[Any, ...], Any]:
        """
        Find user cellphone number.
        :param username: Username that we want his number.
        :return: Cellphone number of the user.
        """
        try:
            query_ref = self.db.collection('Users').where('username', '==', username).get()
            cell = query_ref[0].to_dict()['cellphone']
            return cell
        except Exception as e:
            return e.args

    def get_images(self) -> Union[Iterator, tuple[Any, ...]]:
        """
        Get all images of the house.
        :return: Images files
        """
        try:
            files = self.bucket.list_blobs()
            return files
        except Exception as e:
            return e.args

    def update_user(self, **kwargs) -> Union[tuple[Any, ...], str]:
        """
        Update user field in database.
        :param kwargs: Fields to update
        :return: Status of update.
        """
        try:
            query_ref = self.db.collection('Users').where('username', '==', kwargs['username']).get()
            for doc in query_ref:
                doc_id = doc.id
                self.db.collection("Users").document(doc_id).set(kwargs)
                return "Updated successfully"
        except Exception as e:
            return e.args

    def get_all_users(self):
        """
        Get all user from database.
        :return: User registered from database.
        """
        try:
            query = self.db.collection('Users').get()
            users_details = [user.to_dict() for user in query]
            return users_details
        except Exception as e:
            return e.args

    def create_chat(self, sender:str, receiver: str) -> None:
        """
        Create chat between two users give each user key for their chat table.
        :param sender: The user who opened the chat.
        :param receiver: The user that receive the message.
        """
        chat_ref = self.db.collection('Chats').add({'contacts': {'user_1': sender, 'user_2': receiver}})
        query_ref = self.db.collection('Users').where('username', '==', sender).get()[0].id

        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M:%S")

        self.db.collection('Users').document(query_ref).collection('chats').document(chat_ref[1].id) \
            .set({'last_message': '',
                  'created_time': current_time,
                  'receiver': receiver})

        query_ref = self.db.collection('Users').where('username', '==', receiver).get()[0].id
        self.db.collection('Users').document(query_ref).collection('chats').document(chat_ref[1].id) \
            .set({'last_message': '',
                  'created_time': current_time,
                  'receiver': sender})

    def send_message(self, sender: str, receiver: str, message: str)->None:
        """
        Send message between two users, adds message to their chat table.
        :param sender: The user who send the message.
        :param receiver: The user who receive the message.
        :param message: The message sent.
        """
        sender_id = self.db.collection('Users').where('username', '==', sender).get()[0].id
        receiver_id = self.db.collection('Users').where('username', '==', receiver).get()[0].id
        chat_id = self.db.collection('Users').document(sender_id).collection('chats').where('receiver', '==', receiver).get()[0].id

        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M:%S")

        self.db.collection('Chats').document(chat_id).collection('conversation').add({'message': message,
                                                                                      'sender': sender,
                                                                                      'receiver': receiver,
                                                                                      'date': current_time})

        self.db.collection('Users').document(sender_id).collection('chats').document(chat_id) \
            .set({'last_message': message, 'receiver': receiver})
        self.db.collection('Users').document(receiver_id).collection('chats').document(chat_id) \
            .set({'last_message': message, 'receiver': sender})

    def load_chat(self, user1: str, user2: str) -> List[Dict]:
        """
        Load conversation between two users.
        :param user1: User 1
        :param user2: User 2
        :return : All messages in chat conversation.
        """
        sender_id = self.db.collection('Users').where('username', '==', user1).get()[0].id
        chat_id = self.db.collection('Users').document(sender_id).collection('chats').where('receiver', '==', user2).get()[0].id
        chat_ref = self.db.collection('Chats').document(chat_id).collection('conversation').get()
        chat_messages = [user.to_dict() for user in chat_ref]
        return chat_messages
