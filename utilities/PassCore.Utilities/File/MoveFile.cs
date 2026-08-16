namespace PassCore.Utilities.File;

public sealed class MoveFile{
    public static void Move(string source, string destination)
    {
        string? parent = Path.GetDirectoryName(destination);
        if (parent is not null){Directory.CreateDirectory(parent);}
        if (System.IO.File.Exists(destination)){System.IO.File.Delete(destination);}

        System.IO.File.Move(source, destination);
    }
}