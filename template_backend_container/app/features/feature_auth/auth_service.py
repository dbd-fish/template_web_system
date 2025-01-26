
import structlog
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db
from app.features.feature_auth.auth_repository import UserRepository
from app.features.feature_auth.schemas.user import UserResponse
from app.features.feature_auth.security import decode_access_token, hash_password
from app.models.user import User

logger = structlog.get_logger()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """トークンから現在のユーザーを取得します。

    トークンをデコードして、その情報をもとにデータベースからユーザーを取得します。
    トークンが無効、またはユーザーが存在しない場合は例外をスローします。

    Args:
        token (Annotated[str, Depends]): Bearerトークン。
        db (AsyncSession): 非同期データベースセッション。

    Returns:
        UserResponse: 現在のユーザー情報（Pydanticスキーマ形式）。

    Raises:
        HTTPException:
            - 401: トークンが無効または`sub`フィールドが存在しない場合。
            - 404: ユーザーが存在しない場合。

    """
    logger.info("get_current_user - start")
    try:
        # リクエストヘッダーからCookieを取得
        cookie_header = request.headers.get("cookie")
        logger.info("get_me - cookie_header", cookie_header=cookie_header)
        if not cookie_header:
            logger.warning("get_me - no cookie found")
            raise HTTPException(
                status_code=401, detail="Authentication credentials were not provided"
            )

        # Cookieから`authToken`を抽出
        cookies = {cookie.split("=")[0].strip(): cookie.split("=")[1].strip() for cookie in cookie_header.split(";")}
        logger.info("get_me - cookies", cookies=cookies)
        token = cookies.get("authToken")
        logger.info("get_me - token", token=token)

        if not token:
            logger.warning("get_me - authToken not found in cookies")
            raise HTTPException(
                status_code=401, detail="Authentication credentials were not provided"
            )


        # トークンをデコードしてペイロードを取得
        payload = decode_access_token(token)
        email: str = payload.get("sub") or ""
        if email is None:
            logger.warning("get_current_user - token missing 'sub'", token=token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # TODO: クライアントのIPチェックはプロキシなどの環境に依存するため保留
        client_ip: str = payload.get("client_ip") or ""
        logger.debug("get_current_user - client_ip", client_ip=client_ip)

        # ユーザーをデータベースから取得
        user = await UserRepository.get_user_by_email(db, email)
        if user is None:
            logger.warning("get_current_user - user not found", email=email)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found",
            )

        logger.info("get_current_user - success", user_id=user.user_id)
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            user_role=user.user_role,
            user_status=user.user_status,
        )
    finally:
        logger.info("get_current_user - end")


async def create_user(
    email: str, username: str, password: str, db: AsyncSession,
) -> User:
    """新しいユーザーを作成します。

    ユーザーの情報をもとに新しいユーザーをデータベースに登録します。
    パスワードはハッシュ化されて保存されます。
    エラーが発生した場合はロールバックし、例外をスローします。

    Args:
        email (str): ユーザーのメールアドレス。
        username (str): ユーザー名。
        password (str): プレーンテキストのパスワード。
        db (AsyncSession): 非同期データベースセッション。

    Returns:
        User: 作成されたユーザーオブジェクト。

    Raises:
        HTTPException: ユーザー作成中に発生したエラー。

    """
    logger.info("create_user - start", email=email, username=username)
    try:
        # パスワードをハッシュ化
        hashed_password = hash_password(password)

        # 新しいユーザーオブジェクトを作成
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            user_role=User.ROLE_FREE,
            user_status=User.STATUS_ACTIVE,
        )

        # 既存ユーザーの確認
        existing_user = await UserRepository.get_user_by_email(db, email)
        if existing_user:
            logger.warning("create_user - user already exists", email=email)
            raise HTTPException(
                status_code=400,
                detail="User already exists",
            )

        # データベースにユーザーを保存
        saved_user = await UserRepository.create_user(db, new_user)
        logger.info("create_user - success", user_id=saved_user.user_id)
        return saved_user
    finally:
        logger.info("create_user - end")


async def reset_password(email: str, new_password: str, db: AsyncSession):
    """パスワードをリセットします。

    Args:
        email (str): ユーザーのメールアドレス。
        new_password (str): 新しいプレーンテキストのパスワード。
        db (AsyncSession): 非同期データベースセッション。

    Returns:
        User: パスワードが更新されたユーザーオブジェクト。

    Raises:
        HTTPException: ユーザーが存在しない場合。

    """
    logger.info("reset_password - start", email=email)
    user = await UserRepository.get_user_by_email(db, email)

    if not user:
        logger.info("reset_password - user not found", email=email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    hashed_password = hash_password(new_password)

    try:
        # TODO: メールによるユーザ認証後にパスワード変更を完了するべきでは？
        updated_user = await UserRepository.update_user_password(db, user, hashed_password)
        logger.info("reset_password - success", user_id=updated_user.user_id)
        return updated_user
    except Exception as e:
        logger.error("reset_password - error", error=str(e))
        await db.rollback()
        raise e
    finally:
        logger.info("reset_password - end")
