from django.core.management.base import BaseCommand
from django.utils.text import slugify
from ...models import Article  # Replace 'yourapp' with your actual app name
import json

class Command(BaseCommand):
    help = 'Creates sample articles with translations and quizzes'

    def handle(self, *args, **options):
        articles_data = [
            {
                "title": {
                    "en": "Effective Communication in Relationships",
                    "fr": "Communication efficace dans les relations",
                    "de": "Effektive Kommunikation in Beziehungen"
                },
                "subtitle": {
                    "en": "Building stronger bonds through better dialogue",
                    "fr": "Construire des liens plus forts grâce à un meilleur dialogue",
                    "de": "Stärkere Bindungen durch besseren Dialog aufbauen"
                },
                "body": {
                    "en": "<h1>Effective Communication in Relationships</h1><p>Communication is the cornerstone of any healthy relationship. Here are some key points to remember:</p><ul><li>Listen actively without interrupting</li><li>Express your feelings using 'I' statements</li><li>Avoid blame and criticism</li><li>Practice empathy and understanding</li></ul>",
                    "fr": "<h1>Communication efficace dans les relations</h1><p>La communication est la pierre angulaire de toute relation saine. Voici quelques points clés à retenir :</p><ul><li>Écoutez activement sans interrompre</li><li>Exprimez vos sentiments en utilisant des déclarations 'Je'</li><li>Évitez les reproches et les critiques</li><li>Pratiquez l'empathie et la compréhension</li></ul>",
                    "de": "<h1>Effektive Kommunikation in Beziehungen</h1><p>Kommunikation ist der Grundstein jeder gesunden Beziehung. Hier sind einige wichtige Punkte, die Sie sich merken sollten:</p><ul><li>Hören Sie aktiv zu, ohne zu unterbrechen</li><li>Drücken Sie Ihre Gefühle mit 'Ich'-Aussagen aus</li><li>Vermeiden Sie Schuldzuweisungen und Kritik</li><li>Üben Sie Empathie und Verständnis</li></ul>"
                },
                "author_name": "Dr. Emily Johnson",
                "color": "#E6F3FF",
                "quiz": self.generate_quiz(
                    "Effective Communication",
                    "Communication efficace",
                    "Effektive Kommunikation"
                )
            },
            {
                "title": {
                    "en": "Setting and Achieving Couple Goals",
                    "fr": "Définir et atteindre des objectifs de couple",
                    "de": "Paarziele setzen und erreichen"
                },
                "subtitle": {
                    "en": "Working together towards shared dreams",
                    "fr": "Travailler ensemble vers des rêves communs",
                    "de": "Gemeinsam auf geteilte Träume hinarbeiten"
                },
                "body": {
                    "en": "<h1>Setting and Achieving Couple Goals</h1><p>Setting goals together can strengthen your relationship. Here's how:</p><ul><li>Discuss your individual and shared aspirations</li><li>Set SMART (Specific, Measurable, Achievable, Relevant, Time-bound) goals</li><li>Create an action plan together</li><li>Regularly check in on your progress</li></ul>",
                    "fr": "<h1>Définir et atteindre des objectifs de couple</h1><p>Définir des objectifs ensemble peut renforcer votre relation. Voici comment :</p><ul><li>Discutez de vos aspirations individuelles et communes</li><li>Fixez des objectifs SMART (Spécifiques, Mesurables, Atteignables, Pertinents, Temporellement définis)</li><li>Créez un plan d'action ensemble</li><li>Faites régulièrement le point sur vos progrès</li></ul>",
                    "de": "<h1>Paarziele setzen und erreichen</h1><p>Gemeinsame Ziele zu setzen kann Ihre Beziehung stärken. Hier ist, wie es geht:</p><ul><li>Besprechen Sie Ihre individuellen und gemeinsamen Bestrebungen</li><li>Setzen Sie SMART-Ziele (Spezifisch, Messbar, Erreichbar, Relevant, Terminiert)</li><li>Erstellen Sie gemeinsam einen Aktionsplan</li><li>Überprüfen Sie regelmäßig Ihre Fortschritte</li></ul>"
                },
                "author_name": "Alex and Sam Thompson",
                "color": "#FFF0E6",
                "quiz": self.generate_quiz(
                    "Couple Goals",
                    "Objectifs de couple",
                    "Paarziele"
                )
            },
            {
                "title": {
                    "en": "Building Trust and Accountability",
                    "fr": "Construire la confiance et la responsabilité",
                    "de": "Vertrauen und Verantwortlichkeit aufbauen"
                },
                "subtitle": {
                    "en": "Strengthening your relationship's foundation",
                    "fr": "Renforcer les fondations de votre relation",
                    "de": "Die Grundlage Ihrer Beziehung stärken"
                },
                "body": {
                    "en": "<h1>Building Trust and Accountability</h1><p>Trust and accountability are crucial for a lasting relationship. Consider these points:</p><ul><li>Be consistent in your words and actions</li><li>Take responsibility for your mistakes</li><li>Respect each other's boundaries</li><li>Be transparent about your feelings and decisions</li></ul>",
                    "fr": "<h1>Construire la confiance et la responsabilité</h1><p>La confiance et la responsabilité sont cruciales pour une relation durable. Considérez ces points :</p><ul><li>Soyez cohérent dans vos paroles et vos actes</li><li>Assumez la responsabilité de vos erreurs</li><li>Respectez les limites de l'autre</li><li>Soyez transparent sur vos sentiments et vos décisions</li></ul>",
                    "de": "<h1>Vertrauen und Verantwortlichkeit aufbauen</h1><p>Vertrauen und Verantwortlichkeit sind entscheidend für eine dauerhafte Beziehung. Beachten Sie diese Punkte:</p><ul><li>Seien Sie konsistent in Ihren Worten und Taten</li><li>Übernehmen Sie Verantwortung für Ihre Fehler</li><li>Respektieren Sie die Grenzen des anderen</li><li>Seien Sie transparent in Bezug auf Ihre Gefühle und Entscheidungen</li></ul>"
                },
                "author_name": "Dr. Michael Chen",
                "color": "#E6FFE6",
                "quiz": self.generate_quiz(
                    "Trust and Accountability",
                    "Confiance et responsabilité",
                    "Vertrauen und Verantwortlichkeit"
                )
            }
        ]

        for article_data in articles_data:
            article = Article.objects.create(
                title=article_data["title"],
                subtitle=article_data["subtitle"],
                body=article_data["body"],
                author_name=article_data["author_name"],
                color=article_data["color"],
                quiz=article_data["quiz"],
                slug=slugify(article_data["title"]["en"])
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created article: {article.slug}'))

    def generate_quiz(self, en_title, fr_title, de_title):
        return {
            "en": {
                "title": f"Quiz: {en_title}",
                "questions": [
                    {
                        "question": "What is a key aspect of effective communication?",
                        "options": ["Interrupting", "Active listening", "Criticism", "Ignoring"],
                        "correct_answer": 1
                    },
                    {
                        "question": "How can you express your feelings more effectively?",
                        "options": ["Using 'you' statements", "Using 'I' statements", "Avoiding expressions", "Shouting"],
                        "correct_answer": 1
                    },
                    {
                        "question": "What should you avoid in communication?",
                        "options": ["Empathy", "Understanding", "Blame", "Clarity"],
                        "correct_answer": 2
                    },
                    {
                        "question": "What does SMART stand for in goal setting?",
                        "options": ["Simple, Motivating, Achievable, Realistic, Timed", "Specific, Measurable, Achievable, Relevant, Time-bound", "Strategic, Manageable, Actionable, Reasonable, Trackable", "Shared, Meaningful, Aspirational, Rewarding, Tangible"],
                        "correct_answer": 1
                    },
                    {
                        "question": "How can you build trust in a relationship?",
                        "options": ["Being inconsistent", "Hiding your feelings", "Taking responsibility for mistakes", "Ignoring boundaries"],
                        "correct_answer": 2
                    }
                ]
            },
            "fr": {
                "title": f"Quiz : {fr_title}",
                "questions": [
                    {
                        "question": "Quel est un aspect clé d'une communication efficace ?",
                        "options": ["Interrompre", "L'écoute active", "La critique", "Ignorer"],
                        "correct_answer": 1
                    },
                    {
                        "question": "Comment pouvez-vous exprimer vos sentiments plus efficacement ?",
                        "options": ["En utilisant des déclarations 'vous'", "En utilisant des déclarations 'je'", "En évitant les expressions", "En criant"],
                        "correct_answer": 1
                    },
                    {
                        "question": "Que devez-vous éviter dans la communication ?",
                        "options": ["L'empathie", "La compréhension", "Le blâme", "La clarté"],
                        "correct_answer": 2
                    },
                    {
                        "question": "Que signifie SMART dans la définition des objectifs ?",
                        "options": ["Simple, Motivant, Atteignable, Réaliste, Temporel", "Spécifique, Mesurable, Atteignable, Pertinent, Temporellement défini", "Stratégique, Gérable, Actionnable, Raisonnable, Traçable", "Partagé, Significatif, Ambitieux, Gratifiant, Tangible"],
                        "correct_answer": 1
                    },
                    {
                        "question": "Comment pouvez-vous établir la confiance dans une relation ?",
                        "options": ["En étant incohérent", "En cachant vos sentiments", "En assumant la responsabilité de vos erreurs", "En ignorant les limites"],
                        "correct_answer": 2
                    }
                ]
            },
            "de": {
                "title": f"Quiz: {de_title}",
                "questions": [
                    {
                        "question": "Was ist ein wichtiger Aspekt effektiver Kommunikation?",
                        "options": ["Unterbrechen", "Aktives Zuhören", "Kritik", "Ignorieren"],
                        "correct_answer": 1
                    },
                    {
                        "question": "Wie können Sie Ihre Gefühle effektiver ausdrücken?",
                        "options": ["Mit 'Du'-Aussagen", "Mit 'Ich'-Aussagen", "Ausdrücke vermeiden", "Schreien"],
                        "correct_answer": 1
                    },
                    {
                        "question": "Was sollten Sie in der Kommunikation vermeiden?",
                        "options": ["Empathie", "Verständnis", "Schuldzuweisungen", "Klarheit"],
                        "correct_answer": 2
                    },
                    {
                        "question": "Wofür steht SMART bei der Zielsetzung?",
                        "options": ["Simpel, Motivierend, Erreichbar, Realistisch, Terminiert", "Spezifisch, Messbar, Erreichbar, Relevant, Terminiert", "Strategisch, Managebar, Aktionierbar, Realistisch, Trackbar", "Geteilt, Bedeutsam, Ambitioniert, Belohnend, Tastbar"],
                        "correct_answer": 1
                    },
                    {
                        "question": "Wie können Sie Vertrauen in einer Beziehung aufbauen?",
                        "options": ["Inkonsistent sein", "Gefühle verbergen", "Verantwortung für Fehler übernehmen", "Grenzen ignorieren"],
                        "correct_answer": 2
                    }
                ]
            }
        }