'  **********************************************************************
' 
'  Copyright (c) 2003-2005 ZeroC, Inc. All rights reserved.
' 
'  This copy of Ice is licensed to you under the terms described in the
'  ICE_LICENSE file included in this distribution.
' 
'  **********************************************************************

Imports System

Public NotInheritable Class SessionManagerI
    Inherits Glacier2._SessionManagerDisp

    Public Overloads Overrides Function create(ByVal userId As String, ByVal current As Ice.Current) As Glacier2.SessionPrx
        Console.WriteLine("creating session for user `" & userId & "'")
        Dim session As Glacier2.Session = New SessionI(userId)
        Return Glacier2.SessionPrxHelper.uncheckedCast(current.adapter.addWithUUID(session))
    End Function

End Class
