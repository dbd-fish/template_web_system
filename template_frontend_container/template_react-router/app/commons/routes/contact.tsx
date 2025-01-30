import Header from '~/commons/components/Header';
import Footer from '~/commons/components/Footer';
import { LoaderFunction, redirect, ActionFunction } from 'react-router';
import { userDataLoader } from '~/features/auth_user/loaders/userDataLoader';
import { AuthenticationError } from '~/commons/utils/errors/AuthenticationError';
import { logoutAction } from '~/features/auth_user/actions/logoutAction';
// import logger from '~/commons/utils/logger';

/**
 * ローダー関数:
 * - サーバーサイドで実行され、ユーザー情報を取得
 * - 成功時: ユーザー情報を返す
 * - 失敗時: 401エラーをスロー
 */
export const loader: LoaderFunction = async ({ request }) => {
  // logger.info('[Home Loader] start');
  try {
    const userData = await userDataLoader(request, false);
    const responseBody = {
      user: userData,
    };
    // logger.info('[Home Loader] Successfully retrieved user data');
    // logger.debug('[Home Loader] User data', { userData });

    // 正常なレスポンスを返す
    return new Response(JSON.stringify(responseBody), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AuthenticationError) {
      // logger.warn('[Home Loader] AuthenticationError occurred');
      return redirect('/login');
    }

    // logger.error('[Home Loader] Unexpected error occurred', {
    //   error: error,
    // });

    throw new Response('ユーザーデータの取得に失敗しました。', {
      status: 400,
    });
  } finally {
    // logger.info('[Home Loader] end');
  }
};

// NOTE: ログアウトが必要な画面ではこれと似たAction関数を実装する必要あり
/**
 * アクション関数:
 * - クライアントからのアクションを処理
 * - ログアウトやその他のアクションを処理
 */
export const action: ActionFunction = async ({ request }) => {
  // logger.info('[Home Action] start');
  try {
    const formData = await request.formData();
    const actionType = formData.get('_action');

    // logger.debug('[Home Action] Received actionType', { actionType });

    if (actionType === 'logout') {
      const response = await logoutAction(request);
      // logger.info('[Home Action] Logout action processed successfully');
      return response;
    }

    // logger.warn('[Home Action] No valid actionType provided');
    throw new Response('サーバー上で不具合が発生しました', {
      status: 400,
    });
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (error) {
    // logger.error('[Home Action] Unexpected error occurred', {
    //   error: error
    // });
    throw new Response('サーバー上で予期しないエラーが発生しました', {
      status: 400,
    });
  } finally {
    // logger.info('[Home Action] end');
  }
};

export default function Contact() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-grow bg-gray-100 py-16">
        <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-xl p-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-8 text-center">
            お問い合わせ
          </h1>
          <p className="text-lg text-gray-700 text-center mb-12 leading-relaxed">
            以下のフォームに必要事項をご記入の上、「送信」ボタンを押してください。
            <br />
            お問い合わせ内容を確認後、担当者よりご連絡させていただきます。
          </p>
          <form method="post" className="space-y-10">
            <div>
              <label
                htmlFor="name"
                className="block text-lg font-medium text-gray-800 mb-2"
              >
                お名前 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                required
                className="block w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-lg p-4"
                placeholder="例: 山田 太郎"
              />
            </div>
            <div>
              <label
                htmlFor="email"
                className="block text-lg font-medium text-gray-800 mb-2"
              >
                メールアドレス <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                required
                className="block w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-lg p-4"
                placeholder="例: example@example.com"
              />
            </div>
            <div>
              <label
                htmlFor="message"
                className="block text-lg font-medium text-gray-800 mb-2"
              >
                メッセージ <span className="text-red-500">*</span>
              </label>
              <textarea
                id="message"
                name="message"
                rows={6}
                required
                className="block w-full rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-lg p-4"
                placeholder="お問い合わせ内容をご記入ください"
              ></textarea>
            </div>
            <div className="text-center">
              <button
                type="submit"
                className="inline-flex justify-center px-8 py-4 text-white bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none text-lg font-medium rounded-lg shadow-lg"
              >
                送信する
              </button>
            </div>
          </form>
        </div>
      </main>
      <Footer />
    </div>
  );
}
