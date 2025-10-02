# limpar_migracoes.py
import os
import glob

# Lista de todos os seus apps
APPS = [
    'clientes',
    'casos',
    'configuracoes',
    'contas',
    'core',
    'equipamentos',
    'notificacoes',
    # Adicione outros apps aqui se criar mais no futuro
]

print("--- INICIANDO LIMPEZA DE MIGRAÇÕES ---")

for app in APPS:
    # Monta o caminho para a pasta de migrações do app
    migrations_path = os.path.join(app, 'migrations')
    
    # Verifica se a pasta existe
    if os.path.isdir(migrations_path):
        # Encontra todos os arquivos .py, exceto __init__.py
        files_to_delete = glob.glob(os.path.join(migrations_path, '*.py'))
        pycache_path = os.path.join(migrations_path, '__pycache__')

        for file_path in files_to_delete:
            if not file_path.endswith('__init__.py'):
                try:
                    os.remove(file_path)
                    print(f"  [DELETADO] {file_path}")
                except OSError as e:
                    print(f"  [ERRO] Não foi possível deletar {file_path}: {e}")
        
        # Limpa o cache de migrações também
        if os.path.isdir(pycache_path):
            import shutil
            try:
                shutil.rmtree(pycache_path)
                print(f"  [DELETADO] Pasta __pycache__ em {app}")
            except OSError as e:
                print(f"  [ERRO] Não foi possível deletar a pasta __pycache__ em {app}: {e}")

print("--- LIMPEZA DE MIGRAÇÕES CONCLUÍDA ---")