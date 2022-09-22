# 案件情報定期クローリング

AWSを使用した、案件情報サイトへの定期クローリングと、メール通知処理。

## 全体構成図
![全体構成図](./assets/img/structure.png)

## 通知メールイメージ
![通知メール](./assets/img/mail_arrival.png)
![通知メールCSV](./assets/img/mail_csv.png)

## 構築の流れ
- lambdaレイヤの作成と配置
- lambda関数の作成と配置
- Amazon SESの登録とlambdaの送信先設定
- Amazon EventBridgeのスケジュール設定

## 構築手順詳細
