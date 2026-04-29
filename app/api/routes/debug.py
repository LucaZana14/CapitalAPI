import subprocess

from fastapi import APIRouter, Body, Depends, HTTPException
from starlette import status
from starlette.status import HTTP_400_BAD_REQUEST

from app.api.dependencies.authentication import get_current_user_authorizer

from app.models.domain.users import User
from app.models.schemas.debug import DoExecution, ExecutionInResponse, FlagInResponse

from app.resources.strings import Injection, DescriptionInjection

router = APIRouter()


def execute(cmd):
    # 1. IL BUTTAFUORI: Se non è esattamente "uptime", scartalo e digli cosa è concesso
    if cmd.strip() != "uptime":
        return 0, {"whitelist": {"commands": ['uptime']}}
        
    # 2. L'ESECUZIONE: Se arriva qui, siamo matematicamente certi che il comando è "uptime"
    p = subprocess.Popen(["uptime"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    
    stdout, stderr = p.communicate() 
    
    # 3. IL RISULTATO: Esecuzione andata a buon fine
    if p.returncode == 0:
        return 1, stdout.decode()
    else:
        return 0, "Error"

@router.post(
    "",
    status_code=status.HTTP_200_OK,
    name="debug",
)
async def create_comment_for_article(
        execution: DoExecution = Body(..., embed=True, alias="body"),
        user: User = Depends(get_current_user_authorizer()),
):
    code , stdout = execute(execution.command)
    if code == 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=stdout,
        )
    if code == 1:
        return ExecutionInResponse(stdout=stdout)
    if code == 2:
        return FlagInResponse(
                flag=Injection(),description=DescriptionInjection,stdout=stdout
        )

