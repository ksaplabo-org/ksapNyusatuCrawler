# 案件情報定期クローリング

AWSを使用した、案件情報サイトへの定期クローリングと、メール通知処理。

## 全体構成図
![全体構成図](./assets/img/structure.png)

## 通知メールイメージ
![通知メール](./assets/img/mail_arrival.png)
![通知メールCSV](./assets/img/mail_csv.png)

## 構築の流れ
- lambdaレイヤの作成と配置
- S3バケットの作成とファイル配置
- 「クローリング」lambda関数の作成と配置
- 「通知」lambda関数の作成と配置、Amazon SES設定
- Amazon EventBridgeのスケジュール設定

## 構築手順詳細

<br>

### lambdaレイヤの作成と配置

![awslayer](./assets/img/awsLayer.png)

<br>

#### 背景
クローリングを行うPythonコードでは、selenium等の外部ライブラリを使用しますが、これらはAWS lambdaでは標準提供されていないため、そのままコードを実行すると、no module エラーとなります。

lambda環境で外部ライブラリが使用できるようにするには、開発者自身でライブラリを入手してlambda環境に配置する必要があるのです。

この対応は２つあります。
1. ソースコードと、外部ライブラリをまとめて一つのzipに圧縮し、「lambda - 関数」に登録する。

2. ソースコードと、外部ライブラリをそれぞれ別のzipに圧縮する。外部ライブラリは「lambda - レイヤ」に登録する。ソースコードは「lambda - 関数」に登録しつつ、コード側の設定画面で上記レイヤを使用するように指定する。

手順１の方が簡単ですが、複数のlambda間でライブラリの使い回しができません。また、lambdaのコード画面の制約で、5MBを超えるとソースのかくにん・編集ができなくなる、という問題があり、ライブラリを含めてしまうとこれに該当します。

今回は手順２の方法をとることにします。

<br>

#### 作成するレイヤ
今回のクローリングでは、次のものが必要です。

- pythonライブラリ(lambdaが標準提供してないもの)
  - selenium==4.1
  - requests
  - BeautifulSoup4
  - datetime  

  ※これらは[requirements.txt](./crawlingNyusatuFunc/requirements.txt)に登録しています。

- スクレイピング実行環境
  - chromeブラウザ
  - chromeDriver

<br>

#### 作成方法

レイヤ作成の大きな流れは、次のとおりです。

1. pythonライブラリをpipするためのDocker環境構築 ※
2. Dockerのamazon linux2上でpipコマンドを実行してライブラリ取得
3. ライブラリをzip圧縮する。
4. スクレイピング実行環境のファイルをダウンロードする。
5. スクレイピング実行環境をzip圧縮する。

<h6>※ この手順のとおり、pipコマンドでpythonの外部ライブラリを取得する環境は、Windowsではなく、OS「amazon linux2」互換環境で行うことをお勧めします。pythonの外部ライブラリには、C言語等のOS依存バイナリが使われている場合があるため、Windows環境でpipしたライブラリでレイヤを作ると、lambda環境にアップしても動かない、ということが起こリます。</h6>

ここでは、Layerの作り方は省略します。

1〜3は、[こちらのサイト](https://www.cloudnotes.tech/entry/Lambda_Layer_windows)などを参考に実行してみてください。zip圧縮する際には「python」という名前のディレクトリ（フォルダ）を作ってその中に入れる必要があるので、注意してください。

4〜5の参考サイトは[こちら](https://zenn.dev/eito_blog/articles/72f7b459e2d591)がおすすめです。ポイントとして、バージョン等が非常に重要で、これ以外の環境でやろうとすると激ハマりします。まずは素直に、参考サイトに従うようにしましょう。

今回、作成したzipファイルは、以下にあります。
- pythonライブラリ  
  [./assets/bin/lambda-layer/selenium_layer.zip](./assets/bin/lambda-layer/selenium_layer.zip)

- スクレイピング実行環境  
  [./assets/bin/lambda-layer/headless.zip](./assets/bin/lambda-layer/headless.zip)

<br>

#### レイヤの配置

AWSへのレイヤの登録方法を以下に示します。

- AWSコンソールマネジメントにログインする。
- AWSのサービス一覧で、「AWS lambda」を選択する。
- 左側の「レイヤー」を選び、画面右上にある「レイヤーの作成」をクリックする。
- 以下の設定をして、作成ボタンを押す。
  - 名前：任意
  - アップロードボタンを押して作成したzipファイルを選択
  - 互換性のあるアーキテクチャ：x86_64
  - 互換性のあるランタイム：Python3.7
  ![layer_create](./assets/img/layer_create.png)

上記の手順で、`selenium_layer.zip`と`headless.zip`をそれぞれ登録した、2つのレイヤを作成します。

以上で、「lambdaレイヤの作成と配置」は終了です。

<br>

### S3バケットの作成とファイル配置

後述のクローリング処理が必要とするファイルを、S3上に配置します。

- AWSコンソールマネジメントにログインする。
- AWSのサービス一覧で、「S3」を選択する。
- 左側の「バケット」を選び、画面右上にある「バケットを作成」をクリックする。
- 任意のバケット名を入れて、右下にある「バケットを作成」をクリックする。
- 作成したバケットを選択して、その中にフォルダ「url」を作成する。
- 「url/」フォルダの中に、以下のファイルをアップロードする。
  - クローリング対象のURL一覧csv  
    [/crawlingNyusatuFunc/url/url.csv](/crawlingNyusatuFunc/url/url.csv)

以上で、S3バケットの準備は終了です。

<br>

### 「クローリング」lambda関数の作成と配置

![lambdafunc](/assets/img/awsLambdafunc.png)

クローリングを実行するlambda関数を作成します。コードは、以下のパスの内容となります。

- 「クローリング」lambda関数  
  - [/crawlingNyusatuFunc/lambda_function.py](/crawlingNyusatuFunc/lambda_function.py)
  - [/crawlingNyusatuFunc/crawlingBid.py](/crawlingNyusatuFunc/crawlingBid.py)

このコードをAWS lambda関数に登録していきます。   

<br>

#### ソースコードをzip圧縮

最初に、ローカル環境で、上記2つのファイルを、zipファイルとして圧縮しておいてください。（zip内にフォルダを作らないよう、注意してください）

<br>

#### lambda関数の新規作成

以下の手順で、lambda関数を新たに構築します。

- AWSコンソールマネジメントにログインする。
- AWSのサービス一覧で、「Lambda」を選択する。
- 左側の「関数」を選び、画面右上にある「関数の作成」をクリックする。
- 「関数の作成」画面で、以下の設定を行なって「関数の作成」ボタンをクリックする。
  - 以下のいずれかのオプションを〜：一から作成
  - 関数名：任意。
  - ランタイム：Python3.7
  - アーキテクチャ：x86_64

しばらくすると、lambda関数が作成され、関数の編集画面に遷移します。最初にzip圧縮したソースコードを、この編集画面にアップロードします。

- 編集画面中頃にあるタブの一覧から、「コード」を選択する。
- 右端の「アップロード元」-「zipファイル」選択する。
- アップロードボタンを押して前述のzipファイルを選択し「保存」ボタンをクリックする。
- 「コード」の画面左側のツリーに、前述の２つの.pyファイルが表示されていれば、アップロード完了。

![code](/assets/img/awsLambdafunc_code.png)

<br>

#### lambda関数の設定変更

- zipをアップロード
- レイヤの選択
- 環境変数の設定
- 設定変更
  - ロールポリシーのアタッチ(AmazonS3FullAccess)
  -