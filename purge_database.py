#!/usr/bin/env python3
"""
Script de purge de la base de données SQLite
Utilise avec précaution - données non récupérables après purge!
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = "jurisbot_ci.db"

def backup_database():
    """Crée une sauvegarde avant purge"""
    if not os.path.exists(DB_PATH):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"jurisbot_ci_backup_{timestamp}.db"

    try:
        with open(DB_PATH, 'rb') as original:
            with open(backup_path, 'wb') as backup:
                backup.write(original.read())
        print(f"✅ Sauvegarde créée: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return None

def purge_all_data():
    """Purge TOUS les données"""
    if not os.path.exists(DB_PATH):
        print("❌ Base de données non trouvée")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Vider les tables
        cursor.execute("DELETE FROM responses")
        cursor.execute("DELETE FROM feedbacks")
        cursor.execute("DELETE FROM alerts")
        cursor.execute("DELETE FROM chat_sessions")

        conn.commit()

        # Obtenir les comptes
        cursor.execute("SELECT COUNT(*) FROM responses")
        responses_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM feedbacks")
        feedbacks_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alerts_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        sessions_count = cursor.fetchone()[0]

        conn.close()

        print(f"✅ Base de données purgée:")
        print(f"   • Réponses: {responses_count}")
        print(f"   • Feedbacks: {feedbacks_count}")
        print(f"   • Alertes: {alerts_count}")
        print(f"   • Sessions: {sessions_count}")
        return True
    except Exception as e:
        print(f"❌ Erreur purge: {e}")
        return False

def purge_table(table_name):
    """Purge une table spécifique"""
    valid_tables = ["responses", "feedbacks", "alerts", "chat_sessions"]

    if table_name not in valid_tables:
        print(f"❌ Table invalide. Options: {', '.join(valid_tables)}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        conn.close()
        print(f"✅ Table '{table_name}' purgée (0 enregistrement)")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def get_db_stats():
    """Affiche les statistiques avant purge"""
    if not os.path.exists(DB_PATH):
        print("❌ Base de données non trouvée")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM responses")
        responses_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM feedbacks")
        feedbacks_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alerts_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        sessions_count = cursor.fetchone()[0]

        conn.close()

        print("\n📊 État actuel de la base de données:")
        print(f"   • Réponses: {responses_count}")
        print(f"   • Feedbacks: {feedbacks_count}")
        print(f"   • Alertes: {alerts_count}")
        print(f"   • Sessions: {sessions_count}")
        print(f"   • Total: {responses_count + feedbacks_count + alerts_count + sessions_count}\n")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    import sys

    print("\n🗑️  PURGE DE LA BASE DE DONNÉES - JurisBot CI\n")

    # Afficher l'état
    get_db_stats()

    if len(sys.argv) > 1:
        action = sys.argv[1].lower()

        if action == "all":
            # Purge complète
            print("⚠️  ATTENTION: Cette action va SUPPRIMER TOUTES les données!")
            confirm = input("Êtes-vous sûr? (tapez 'oui' pour confirmer): ").strip().lower()

            if confirm == "oui":
                backup_path = backup_database()
                if purge_all_data():
                    print(f"\n✅ Purge complète réussie!")
                    if backup_path:
                        print(f"📦 Sauvegarde disponible: {backup_path}")
            else:
                print("❌ Purge annulée")

        elif action in ["responses", "feedbacks", "alerts", "chat_sessions"]:
            # Purge d'une table
            backup_path = backup_database()
            if purge_table(action):
                print(f"\n✅ Purge de '{action}' réussie!")
                if backup_path:
                    print(f"📦 Sauvegarde disponible: {backup_path}")

        elif action == "backup":
            # Juste faire une sauvegarde
            backup_database()

        else:
            print_help()
    else:
        print_help()

def print_help():
    print("""
📋 UTILISATION:
    python purge_database.py [ACTION]

🔧 ACTIONS:
    all                 Purge TOUTES les données
    responses          Purge uniquement les réponses
    feedbacks          Purge uniquement les feedbacks
    alerts             Purge uniquement les alertes
    chat_sessions      Purge uniquement les sessions
    backup             Crée juste une sauvegarde

⚠️  EXEMPLES:
    # Voir l'état actuel
    python purge_database.py

    # Créer une sauvegarde
    python purge_database.py backup

    # Purger toutes les données
    python purge_database.py all

    # Purger juste les feedbacks
    python purge_database.py feedbacks

🛡️  Tous les appels créent une sauvegarde automatiquement!
""")

if __name__ == "__main__":
    main()
