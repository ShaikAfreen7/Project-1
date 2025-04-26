
from django.db.models import  Count, Avg
from django.shortcuts import render, redirect
from django.db.models import Count
from django.db.models import Q
import datetime
import xlwt
from django.http import HttpResponse


import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

from nltk.tokenize import word_tokenize
import string
from nltk.stem import WordNetLemmatizer
import nltk
nltk.download('wordnet')
#nltk.download('stopwords')
from nltk.corpus import stopwords

# Create your views here.
from Remote_User.models import ClientRegister_Model,detect_mental_health,detection_ratio,detection_accuracy


def serviceproviderlogin(request):
    if request.method  == "POST":
        admin = request.POST.get('username')
        password = request.POST.get('password')
        if admin == "Admin" and password =="Admin":
            detection_accuracy.objects.all().delete()
            return redirect('View_Remote_Users')

    return render(request,'SProvider/serviceproviderlogin.html')

def View_Predicted_Mental_Health_Type_Ratio(request):
    detection_ratio.objects.all().delete()
    ratio = ""
    kword = 'Depression'
    print(kword)
    obj = detect_mental_health.objects.all().filter(Q(Prediction=kword))
    obj1 = detect_mental_health.objects.all()
    count = obj.count();
    count1 = obj1.count();
    ratio = (count / count1) * 100
    if ratio != 0:
        detection_ratio.objects.create(names=kword, ratio=ratio)

    ratio12 = ""
    kword12 = 'No Depression'
    print(kword12)
    obj12 = detect_mental_health.objects.all().filter(Q(Prediction=kword12))
    obj112 = detect_mental_health.objects.all()
    count12 = obj12.count();
    count112 = obj112.count();
    ratio12 = (count12 / count112) * 100
    if ratio12 != 0:
        detection_ratio.objects.create(names=kword12, ratio=ratio12)


    obj = detection_ratio.objects.all()
    return render(request, 'SProvider/View_Predicted_Mental_Health_Type_Ratio.html', {'objs': obj})

def View_Remote_Users(request):
    obj=ClientRegister_Model.objects.all()
    return render(request,'SProvider/View_Remote_Users.html',{'objects':obj})

def charts(request,chart_type):
    chart1 = detection_ratio.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request,"SProvider/charts.html", {'form':chart1, 'chart_type':chart_type})

def charts1(request,chart_type):
    chart1 = detection_accuracy.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request,"SProvider/charts1.html", {'form':chart1, 'chart_type':chart_type})

def View_Predicted_Mental_Health_Type_Details(request):
    obj =detect_mental_health.objects.all()
    return render(request, 'SProvider/View_Predicted_Mental_Health_Type_Details.html', {'list_objects': obj})

def likeschart(request,like_chart):
    charts =detection_accuracy.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request,"SProvider/likeschart.html", {'form':charts, 'like_chart':like_chart})


def Download_Predicted_DataSets(request):

    response = HttpResponse(content_type='application/ms-excel')
    # decide file name
    response['Content-Disposition'] = 'attachment; filename="Predicted_Datasets.xls"'
    # creating workbook
    wb = xlwt.Workbook(encoding='utf-8')
    # adding sheet
    ws = wb.add_sheet("sheet1")
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True
    # writer = csv.writer(response)
    obj = detect_mental_health.objects.all()
    data = obj  # dummy method to fetch data.
    for my_row in data:

        row_num = row_num + 1

        ws.write(row_num, 0, my_row.Post, font_style)
        ws.write(row_num, 1, my_row.DateTime, font_style)
        ws.write(row_num, 2, my_row.Prediction, font_style)

    wb.save(response)
    return response

def train_model(request):
    detection_accuracy.objects.all().delete()

    df = pd.read_csv('Datasets.csv',encoding='latin-1')

    # data under nlp
    print("Data Processing Under Natural Language Processing (NLP)")
    data = []
    Labels = []
    # Data Processing Under Natural Language Processing (NLP)
    for row in df["Posts"]:
        # tokenize words
        words = word_tokenize(row)
        # remove punctuations
        clean_words = [word.lower() for word in words if word not in set(string.punctuation)]
        # remove stop words
        english_stops = set(stopwords.words('english'))
        characters_to_remove = ["''", '``', "rt", "https", "â€™", "â€œ", "â€", "\u200b", "--", "n't", "'s",
                                "...",
                                "//t.c"]
        clean_words = [word for word in clean_words if word not in english_stops]
        clean_words = [word for word in clean_words if word not in set(characters_to_remove)]
        # Lematise words
        wordnet_lemmatizer = WordNetLemmatizer()
        lemma_list = [wordnet_lemmatizer.lemmatize(word) for word in clean_words]
        data.append(lemma_list)

    def apply_results(label):
        if (label == 0):
            return 0  # No Depression
        elif (label == 1):
            return 1  # Depression

    df['results'] = df['label'].apply(apply_results)

    X = df['Posts']
    y = df['results']

    print("Post Desc")
    print(X)
    print("Results")
    print(y)

    cv = CountVectorizer()
    X = cv.fit_transform(X)

    models = []
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20)
    X_train.shape, X_test.shape, y_train.shape

    print("Convolutional Neural Network--CNN")
    from sklearn.neural_network import MLPClassifier
    mlpc = MLPClassifier().fit(X_train, y_train)
    y_pred = mlpc.predict(X_test)
    testscore_mlpc = accuracy_score(y_test, y_pred)
    accuracy_score(y_test, y_pred)
    print(accuracy_score(y_test, y_pred))
    print(accuracy_score(y_test, y_pred) * 100)
    print("CLASSIFICATION REPORT")
    print(classification_report(y_test, y_pred))
    print("CONFUSION MATRIX")
    print(confusion_matrix(y_test, y_pred))
    models.append(('MLPClassifier', mlpc))
    detection_accuracy.objects.create(names="Convolutional Neural Network--CNN",
                                      ratio=accuracy_score(y_test, y_pred) * 100)

    print("Extra Tree Classifier")
    from sklearn.tree import ExtraTreeClassifier
    etc_clf = ExtraTreeClassifier()
    etc_clf.fit(X_train, y_train)
    etcpredict = etc_clf.predict(X_test)
    print("ACCURACY")
    print(accuracy_score(y_test, etcpredict) * 100)
    print("CLASSIFICATION REPORT")
    print(classification_report(y_test, etcpredict))
    print("CONFUSION MATRIX")
    print(confusion_matrix(y_test, etcpredict))
    models.append(('RandomForestClassifier', etc_clf))
    detection_accuracy.objects.create(names="Extra Tree Classifier", ratio=accuracy_score(y_test, etcpredict) * 100)

    # SVM Model
    print("SVM")
    from sklearn import svm
    lin_clf = svm.LinearSVC()
    lin_clf.fit(X_train, y_train)
    predict_svm = lin_clf.predict(X_test)
    svm_acc = accuracy_score(y_test, predict_svm) * 100
    print(svm_acc)
    print("CLASSIFICATION REPORT")
    print(classification_report(y_test, predict_svm))
    print("CONFUSION MATRIX")
    print(confusion_matrix(y_test, predict_svm))
    models.append(('svm', lin_clf))
    detection_accuracy.objects.create(names="SVM", ratio=svm_acc)

    print("Logistic Regression")

    from sklearn.linear_model import LogisticRegression
    reg = LogisticRegression(random_state=0, solver='lbfgs').fit(X_train, y_train)
    y_pred = reg.predict(X_test)
    print("ACCURACY")
    print(accuracy_score(y_test, y_pred) * 100)
    print("CLASSIFICATION REPORT")
    print(classification_report(y_test, y_pred))
    print("CONFUSION MATRIX")
    print(confusion_matrix(y_test, y_pred))
    models.append(('logistic', reg))
    detection_accuracy.objects.create(names="Logistic Regression", ratio=accuracy_score(y_test, y_pred) * 100)

    print("Random Forest Classifier")
    from sklearn.ensemble import RandomForestClassifier
    rf_clf = RandomForestClassifier()
    rf_clf.fit(X_train, y_train)
    rfpredict = rf_clf.predict(X_test)
    print("ACCURACY")
    print(accuracy_score(y_test, rfpredict) * 100)
    print("CLASSIFICATION REPORT")
    print(classification_report(y_test, rfpredict))
    print("CONFUSION MATRIX")
    print(confusion_matrix(y_test, rfpredict))
    models.append(('RandomForestClassifier', rf_clf))
    detection_accuracy.objects.create(names="Random Forest Classifier", ratio=accuracy_score(y_test, rfpredict) * 100)

    print("Gradient Boosting Classifier")

    from sklearn.ensemble import GradientBoostingClassifier
    clf = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0, max_depth=1, random_state=0).fit(
        X_train,
        y_train)
    clfpredict = clf.predict(X_test)
    print("ACCURACY")
    print(accuracy_score(y_test, clfpredict) * 100)
    print("CLASSIFICATION REPORT")
    print(classification_report(y_test, clfpredict))
    print("CONFUSION MATRIX")
    print(confusion_matrix(y_test, clfpredict))
    models.append(('GradientBoostingClassifier', clf))
    detection_accuracy.objects.create(names="Gradient Boosting Classifier",
                                      ratio=accuracy_score(y_test, clfpredict) * 100)

    csv_format = 'Results.csv'
    df.to_csv(csv_format, index=False)
    df.to_markdown

    obj = detection_accuracy.objects.all()
    return render(request,'SProvider/train_model.html', {'objs': obj})