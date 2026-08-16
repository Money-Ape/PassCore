namespace PassCore.Utilities.File;

public sealed class DeleteDirectoryContents{
    public static void DDC(string directory){
        if (!Directory.Exists(directory)){return;}

        foreach (string file in Directory.EnumerateFiles(directory, "*", System.IO.SearchOption.AllDirectories)){
            System.IO.File.Delete(file);
        }
        foreach (string dir in Directory.EnumerateDirectories(directory, "*", System.IO.SearchOption.AllDirectories).OrderByDescending(x => x.Length)){
            Directory.Delete(dir);
        }
    }
}