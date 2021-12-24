from sys import path as path
path.append('./')
from app.models.connection_model import DbConnectionModel

class PermisosModel(DbConnectionModel):
    INSERT_PERMISO_STMT = 'INSERT INTO permisos(nombre, descripcion) VALUES (%s, %s)'
    UPDATE_NOM_PERMISO_STMT = 'UPDATE permisos SET nombre = %s WHERE id_permiso = %s'
    UPDATE_DESC_PERMISO_STMT = 'UPDATE permisos SET descripcion = %s WHERE id_permiso = %s'
    CONSULT_PERMISO_STMT = 'SELECT * FROM permisos'
    CONSULT_PERMISO_BY_ID_STMT = 'SELECT nombre, descripcion FROM permisos WHERE id_permiso = %s'
    UPDATE_PERMISO_STMT = 'UPDATE permisos SET nombre = %s, descripcion = %s WHERE id_permiso = %s'
    DELETE_PERMISO_STMTS = 'DELETE FROM permisos WHERE id_permiso = %s'

    def consult_permiso_by_id(self, id_permiso):
        try:
            permiso = super().execute_sql_stmt(self.CONSULT_PERMISO_BY_ID_STMT, [id_permiso], True)
            if len(permiso) == 0:
                return None
            return permiso[0]
        except Exception as e:
            raise e

    def update_permiso(self, nombre, decripcion, id_permiso):
        try:
            super().execute_sql_stmt(self.UPDATE_PERMISO_STMT, (nombre, decripcion, id_permiso))
        except Exception as e:
            raise e
    
    def insert_permiso(self, nombre, descripcion):
        try:
            super().execute_sql_stmt(self.INSERT_PERMISO_STMT, (nombre, descripcion))
        except Exception as e:
            raise e
    
    def update_nombre(self, nombre, id_permiso):
        try:
            super().execute_sql_stmt(self.UPDATE_NOM_PERMISO_STMT, (nombre, id_permiso))
        except Exception as e:
            raise e
    
    def update_descripcion(self, descripcion, id_permiso):
        try:
            super().execute_sql_stmt(self.UPDATE_DESC_PERMISO_STMT, (descripcion, id_permiso))
        except Exception as e:
            raise e
    
    def consult_permiso(self):
        try:
            permiso = super().execute_sql_stmt(self.CONSULT_PERMISO_STMT, '', True)
            if len(permiso) == 0:
                return None
            return permiso
        except Exception as e:
            raise e
    
    def delete_permiso(self, id_permiso):
        try:
            super().execute_sql_stmt(self.DELETE_PERMISO_STMTS, [id_permiso])
        except Exception as e:
            raise e