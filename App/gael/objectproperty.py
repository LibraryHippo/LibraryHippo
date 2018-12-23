# directly stolen from
# http://kovshenin.com/archives/app-engine-python-objects-in-the-google-datastore/

from google.appengine.ext import db
import pickle


# Use this property to store objects.
class ObjectProperty(db.BlobProperty):
    def validate(self, value):
        try:
            pickle.dumps(value)
            return value
        except pickle.PicklingError:
            return super(ObjectProperty, self).validate(value)

    def get_value_for_datastore(self, model_instance):
        result = super(ObjectProperty, self).get_value_for_datastore(model_instance)
        result = pickle.dumps(result)
        return db.Blob(result)

    def make_value_from_datastore(self, value):
        try:
            value = pickle.loads(str(value))
        except:  # noqa E722 - there are many exceptions that can be thrown
            pass
        return super(ObjectProperty, self).make_value_from_datastore(value)
