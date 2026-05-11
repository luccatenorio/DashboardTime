import os
import secrets
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

clients_data = [
    ("Samia imoveis", "416373050210995"),
    ("Pedro fiuza", "1431550778137694"),
    ("RGA IMOVEIS", "551050788075535"),
    ("Marcos Sena", "779408463852213"),
    ("Alpha(pix)", "1074806258018130"),
    ("Calebe", "287173276025398"),
    ("Casa Retiro Imoveis", "298405036195752"),
    ("Nicole Auane", "1299410112010370"),
    ("Debora Braga", "2200340743732943"),
    ("Daiane Abreu", "199691101179385"),
    ("Daniel Rocha", "4144351822492621"),
    ("Daniel Reis", "2126689617835960"),
    ("Gabriel Silveira", "1314014302872299"),
    ("Meu AP ONLINE", "954637800477034"),
    ("Adriano Godoi", "5703995869635996"),
    ("ELOS", "2270899649900691"),
    ("Laura Azevedo", "237392926946077"),
    ("Glauber", "869052325628958"),
    ("Leonardo Imoveis", "246551341112390"),
    ("Marcos Souza", "996868725451582"),
    ("PHDLUB", "1153386850002125"),
    ("Rede incidica", "24493941176922637"),
    ("Vicente Shop", "1045246030138172"),
    ("Viva no retiro", "164872344245713"),
    ("YaYa Doceria", "3449420578647581"),
    ("Glenda Sousa", "847967398076695"),
    ("Matheus Pereira", "1293130711283698"),
    ("Vitor Fonseca", "2022096635079945"),
    ("Diego Barbosa", "378570952736384"),
    ("Rafael Remido", "3591091771154934"),
    ("Iury Rodrigues", "795352589807861"),
    ("Caio Ferreira", "678007863814807")
]

def generate_hash():
    return secrets.token_urlsafe(24).replace('-', '').replace('_', '').lower()

def main():
    print("Iniciando adicao em massa de clientes...")
    
    for name, account_id in clients_data:
        # Formatar account_id se necessário (adicionar act_ se não tiver)
        if not account_id.startswith('act_'):
            account_id = f"act_{account_id}"
            
        # Verificar se já existe
        res = supabase.table('clients').select('*').ilike('cliente', name).execute()
        
        if res.data:
            print(f"Cliente '{name}' ja existe. Atualizando conta de anuncio e verificando hash...")
            client_id = res.data[0]['id']
            current_hash = res.data[0].get('observacoes')
            
            update_data = {'conta_anuncio': account_id, 'ativo': True}
            
            if not current_hash or len(current_hash) < 20:
                new_hash = generate_hash()
                update_data['observacoes'] = new_hash
                print(f"   - Gerado novo hash para {name}")
            
            supabase.table('clients').update(update_data).eq('id', client_id).execute()
        else:
            print(f"Adicionando novo cliente: '{name}'")
            new_hash = generate_hash()
            supabase.table('clients').insert({
                'cliente': name,
                'conta_anuncio': account_id,
                'ativo': True,
                'observacoes': new_hash
            }).execute()
            print(f"   - Cliente adicionado com hash: {new_hash}")

    print("\n" + "="*60)
    print("RELATÓRIO DE ACESSO")
    print("="*60)
    
    for name, _ in clients_data:
        res = supabase.table('clients').select('cliente, observacoes').ilike('cliente', name).execute()
        if res.data:
            c = res.data[0]
            print(f"{c['cliente']}: http://localhost:5174/#/c/{c.get('observacoes')}")

if __name__ == "__main__":
    main()
