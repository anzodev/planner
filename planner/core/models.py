import peewee as pw


db = pw.DatabaseProxy()


class BaseModel(pw.Model):
    class Meta:
        database = db


class User(BaseModel):
    class Meta:
        table_name = "users"

    username = pw.CharField(unique=True)
    password_hash = pw.TextField()


class Task(BaseModel):
    class Meta:
        table_name = "tasks"

    user = pw.ForeignKeyField(User)
    parent_task = pw.ForeignKeyField("self", null=True)
    name = pw.TextField()
    note = pw.TextField(null=True)
    progress = pw.DoubleField()
    created_at = pw.DateTimeField()

    def is_completed(self) -> bool:
        return self.progress == 100
